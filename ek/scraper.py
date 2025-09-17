### ek/scraper.py
### Version 1.2.2 

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime
import json
import time
import logging

# polite default UA - change this to your project URL or contact info
HEADERS = {"User-Agent": "RAG-Auditor/1.0 (+https://yourdomain.example)"}
DEFAULT_DELAY = 1.0 # seconds if robots.txt doesn't specify crawl-delay

# cache RobotFileParser instances per domain
_robot_parsers = {}

def make_session(retries=3, backoff_factor=0.5, status_forcelist=(429,500,502,503,504)):
    """Create a requests.Session with retry/backoff behaviour."""
    sess = requests.Session()
    sess.headers.update(HEADERS)

    retry = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=frozenset(["GET", "HEAD"])
    )
    adapter = HTTPAdapter(max_retries=retry)
    sess.mount("https://", adapter)
    sess.mount("http://", adapter)
    return sess

def _get_domain_root(url):
    """helper function-normalize domains for robots.txt and crawl delay."""
    p = urlparse(url)
    return f"{p.scheme}://{p.netloc}"

def get_robot_parser(url):
    """
    return a RobotFileParser for the domain (cached).
    if fetching fails, cache None and allow crawling by default.
    """
    domain_root = _get_domain_root(url)
    if domain_root in _robot_parsers:
        return _robot_parsers[domain_root]

    robots_url = urljoin(domain_root, "/robots.txt")
    rp = RobotFileParser()
    try:
        rp.set_url(robots_url)
        rp.read() #network call to feth robots.txt
        _robot_parsers[domain_root] = rp
        return rp
    except Exception as e:
        logging.debug(f"[robots] failed to read {robots_url}:{e}")
        """ store None to avoid repeated failing reads; None = "no robots info, allow by default"""
        _robot_parsers[domain_root] = None
        return None

def can_fetch(url, user_agent=HEADERS["User-Agent"]):
    rp = get_robot_parser(url)
    if rp is None:
        return True
    try:
        return rp.can_fetch(user_agent, url)
    except Exception:
        return True

def crawl_delay(url, user_agent=HEADERS["User-Agent"]):
    rp = get_robot_parser(url)
    if rp is None:
        return None
    try:
        return rp.crawl_delay(user_agent)
    except Exception:
        return None

def safe_get(session, url, timeout=12):
    """
    Fetch URL using session, but first check robots.txt.
    returns requests.Response or None if blocked/failed.
    """
    if not can_fetch(url):
        logging.info(f"[robots] blocked by robots.txt: {url}")
        return None

    try:
        r = session.get(url, timeout=timeout)
        r.raise_for_status()
        return r
    except requests.RequestException as e:
        logging.warning(f"[fetch] {url} failed: {e}")
        return None

def extract_page(session, url):
    """
    Scrape page using provided session.Returns strucutred dict.
    If fetch fails, returns dict with error key.
    """
    r = safe_get(session, url)
    if r is None:
        return {"url": url,
                "error": "fetch_failed_or_blocked",
                "scraped_at": datetime.utcnow().isoformat()
               }
        
    soup = BeautifulSoup(r.text, "html.parser")

    #remove scripts/styles to avoid noise
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    # Title extraction
    title = (soup.title.string if soup.title else "").strip()

    # Meta description
    md = soup.find("meta", attrs={"name": "description"})
    meta_desc = md["content"].strip() if md and md.get("content") else ""

    # Headings 
    headings = [h.get_text(strip=True) for h in soup.find_all(["h1","h2","h3"])]  # can include h4..h6 for more granularity.

    # Text content // for long pages consider capping length (text[:20000]) or chunking
    paragraphs = [p.get_text(" ", strip=True)for p in soup.find_all("p")] 
    text = "\n".join(paragraphs)[:20000] # cap to avoid enormous blobs

    # Images
    images = []
    for img in soup.find_all("img"):
        src = img.get("src") or ""
        images.append({"src": urljoin(url, src), "alt": img.get("alt", "")})

    # Links
    
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        #normalize to ablosute and skip fragments/javascript/mailto for now
        if href.startswith("javascript:") or href.startswith("mailto:") or href.startswith("tel:"):
            continue
        abs_link = urljoin(url, href)
        links.append(abs_link)

    return {
        "url": url,
        "title": title,
        "meta_description": meta_desc,
        "headings": headings,
        "text": text,
        "images": images,
        "internal_links": links,
        "scraped_at": datetime.utcnow().isoformat()
    }

def polite_sleep(url):
    """Sleep respecting crawl-delay for URLs domain (or DEFAULT_DELAY)"""
    delay = crawl_delay(url)
    if delay is None:
        delay = DEFAULT_DELAY
    try:
        time.sleep(float(delay))
    except Exception:
        time.sleep(DEFAULT_DELAY)
