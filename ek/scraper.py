### Scraper.py
### Version 1.0.0 initial blueprint
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
import json

HEADERS = {"User-Agent": "RAG-Auditor/1.0 (+https://yourdomain.example)"}

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
