# embed_pages.py
# version 1.1.0

import os, json, sqlite3
import logging
from pathlib import Path
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# logging Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# path Setup
DB_PATH = "data/site_pages.sqlite"
FAISS_PATH = "data/faiss_index"

def ensure_data_dir():
  Path("data").mkdir(exist_ok=True)

def load_pages():
  if not os.path.exists(DB_PATH):
    logger.error(f"Database not found: {DB_PATH}")
    return []

  try:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
                SELECT url, text 
                FROM pages 
                WHERE text IS NOT NULL AND TRIM(text) != ''
            """)
    rows = cur.fetchall()
    conn.close()
    pages = [{"url": r[0], "text": r[1]} for r in rows]
    logger.info(f"Loaded {len(pages)} pages from database")
    return pages

  except sqlite3.Error as e:
    logger.error(f"Database error: {e}")
    return []
  except Exception as e:
    logger.error(f"Unexpected error loading pages: {e}")
    return []

def build_faiss(pages):
  """ Build FAISS index and use a small fast model for embeddings """
  if not pages:
    logger.error("No pages to process")
    return False

  try:
    logger.info("Initializing embeddings model...")
    embedder = HuggingFaceEmbeddings(
      model_name="sentence-transformers/all-MiniLM-L6-v2",
      cache_folder="./model_cache"
      )
      docs = []
      metadatas = []

  for page in pages:
    text = page["text"].strip()
    if text:
      docs.append(text)
      metadatas.append({"url": page["url"]})

  if not docs:
    logger.error("No valid documents found after filtering ")
    return False

  logger.info(f"Building FAISS index for {len(docs)} documents...")

  # Build FAISS index 
  db = FAISS.from_texts(docs, embedder, metadatas=metadatas)
  ensure_data_dir()

  # save to disk
  db.save_local(FAISS_PATH)
  logger.info(f" [Success] FAISS index saved at {FAISS_PATH}")
  return True

def main():
  """Main exec function"""
  logger.info("Starting embedding process....")

  # load pages from db
  pages = load_pages()

  if not pages:
    logger.error(" [X] No pages found in DB. Run scrape_site.py first")
    return

  # build and save FAISS index
  success = build_faiss(pages)

  if success:
    logger.info(" [Success] Embedding process completed!")
  else:
    logger.error(" [X] Embedding process failed!")  

if __name__ == "__main__":
    main()
