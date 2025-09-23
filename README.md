# RAG Website Auditor

Audit and analyze websites using **Retrieval-Augmented Generation (RAG)** with FAISS vector search, SQLite storage, and pluggable LLMs (OpenAI or local Hugging Face models).

> **Note:** This project is still under construction. Features, APIs, and scripts may change frequently.

---

## Features

* **Scrape websites** into a structured SQLite database (`site_pages.sqlite`).
* **Store embeddings** in a FAISS vector index (`data/faiss_index`).
* **Query with RAG** using OpenAI or Hugging Face models (Falcon, Mistral, etc.).
* Runs on **CPU or GPU (CUDA)**.
* **Simple modular scripts:**

  * `scripts/scrape_site.py` — scrape a site into SQLite.
  * `scripts/embed_pages.py` — build FAISS embeddings from scraped pages.
  * `scripts/audit_site.py` — query the site with an LLM.

---

## Quick Start

1. **Scrape a site**

   ```bash
   python scripts/scrape_site.py --start https://example.com --db site_pages.sqlite
   ```

2. **Generate embeddings**

   ```bash
   python scripts/embed_pages.py --db site_pages.sqlite --out data/faiss_index
   ```

3. **Run an audit query**

   ```bash
   python scripts/audit_site.py --db site_pages.sqlite --faiss data/faiss_index --model openai
   ```

---

## Project Structure

```
RAG-Website-Auditor/
├── data/
│   └── faiss_index/
│   └──site_pages.sqlite
├── scripts/
│   ├── scrape_site.py
│   ├── embed_pages.py
│   └── audit_site.py
└── ek/
    ├── db.py
    └── scraper.py
```

---

## License

MIT — free to use and modify, but respect robots.txt and site terms when scraping.
