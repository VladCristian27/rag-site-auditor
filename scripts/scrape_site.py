## scrape_site.py
## version 1.0.0

from ek.scraper import extract_page
from ek.db import init_db, upsert_page

URLS = [
    "https://example.com"
    #add more pages here
]


if __name__ == "__main__":
    conn = init_db()
    from url in URLS:
         page = extract_page(url)
         upsert_page(conn, page)
         print(f"Saved: {page['url']}")
