## scrape_site.py
## version 1.1.0

from ek.scraper import make_session, extract_page, polite_sleep
from ek.db import init_db, upsert_page
from urllib.parse import urlparse
from collections import deque
import sys

# CONFIG - tweak here
START_URLS = [
    "https://example.com"
    #add more pages here
]
MAX_PAGES = 10
MAX_DEPTH = 2
SAME_DOMAIN_ONLY = True # only follow links within start domain

def domain_of(url):
    p = urlparse(url)
    return p.netloc.lower()

if __name__ == "__main__":
    #optionally accept start URL from CLI
    if len(sys.argv) > 1:
        START_URLS = [sys.argv[1]]

    conn = init_db()
    session = make_session()

    q = deque()
    for u in START_URLS:
        q.append((u, 0))

    visited = set()
    start_domain = domain_of(START_URLS[0])

    while q and len(visited) < MAX_PAGES:
        url, depth = q.popleft()
        if url in visited:
            continue
        if depth > MAX_DEPTH:
            continue
        #optional same-domain restr.
        if SAME_DOMAIN_ONLY and domain_of(url) != start_domain:
            continue

        page = extract_page(session, url)
        upsert_page(conn, page)
        print(f"Saved: {page.get('url')} (depth={depth})")
        visited.add(url)

        # polite delay per domain
        polite_sleep(url)

        # enqueue links
        for link in page.get("internal_links", []):
            if link in visited:
                continue
            if not link.lower().startwith("http"):
                continue
            q.append((link, depth + 1))
