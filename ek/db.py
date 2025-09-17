## db.py
## 


import sqlite3, json

def init_db(path="data/site_pages.sqlite"):
    conn = sqlite.connect(path)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS pages (
        id INTEGER PRIMARY KEY,
        url TEXT UNIQUE,
        title TEXT,
        meta_description TEXT,
        headings TEXT,
        text TEXT,
        images TEXT,
        internal_links TEXT,
        scraped_at TEXT
    );
    """)
    conn.comit()
    return conn

def upsert_page(conn, page: dict):
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO pages (url,title,meta_description,headings,text,images,internal_links,scraped_at)
    VALUES (?,?,?,?,?,?,?,?)
    ON CONFLICT(url) DO UPDATE SET
        title=excluded.title,
        meta_description=excluded.meta_description,
        headings=excluded.headings,
        text=excluded.text,
        images=excluded.images,
        internal_links=excluded.internal_links,
        scraped_at=excluded.scraped_at;
    """, (
        page["url"],
        page["title"],
        page["meta_description"],
        json.dumps(page["headings"]),
        page["text"],
        json.dumps(page["images"]),
        json.dumps(page["internal_links"]),
        page["scraped_at"]
    ))
    conn.comit()
