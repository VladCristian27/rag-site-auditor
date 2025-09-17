### ek/scraper.py
### Version 1.2.1 

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
        _robot_parser[domain_root] = None
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

def extract_page(url: str) -> dict:
    r = requests.get(url, headers=HEADERS, timeout=12)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    # Title extraction
    title = (soup.title.string if soup.title else "").strip()

    # Meta description
    md = soup.find("meta", attrs={"name": "description"})
    meta_desc = md["content"].strip() if md and md.get("content") else ""

    # Headings 
    headings = [h.get_text(strip=True) for h in soup.find_all(["h1","h2","h3"])]  # can include h4..h6 for more granularity.

    # Text content // for long pages consider capping length (text[:20000]) or chunking
    paragraphs = [p.get_text(" ", strip=True)for p in soup.find_all("p")] 
    text = "\n".join(paragraphs)

    # Images
    images = []
    for img in soup.find_all("img"):
        src = img.get("src") or ""
        images.append({"src": urljoin(url, src), "alt": img.get("alt", "")})

    # Links
    links = [urljoin(url, a["href"]) for a in soup.find_all("a", href=True)]

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

if __name__ == "__main__":
    test_url = "https://example.com"
    data = extract_page(test_url)
    print(json.dumps(data, indent=2))
