# RAG- Website Auditor

Audit and analyze websites using **RAG (Retrieval-Augmented Generation)** with FAISS vector search, SQLite storage, and pluggable LLMs (OpenAI or local HuggingFace)

--
## Features
-*Scrape websites* into a strucutured SQLite database (site_pages.sqlite)
-*Store embeddings* in a FAISS vector index (data/faiss_index)
-*Query with RAG* using OpenAI or local HuggingFace model (Falcon, Mistral, etc)
-Runs on *CPU or GPU (CUDA)*
-Simple modular scripts:
  -'scripts/scrape_site.py' - scrape a site into SQLite
  -'scripts/embed_pages.py' - build FAISS embeddings from scraped pages (FAISS + Embedding LLM(lightweight))
  -'scripts/audit_site.py'  - query the site with LLM Model
--

  
  
 **Note:** This project is still under construction.  
> Features, APIs, and scripts may change frequently.
