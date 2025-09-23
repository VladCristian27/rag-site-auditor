# scripts/audit_site.py
# version 1.1.2 - fixed faiss loading issue

import os
import logging
from langchain.chains import RetrievalQA
from langchain_community.vectorstores import FAISS
from langchain_community.llms import HuggingFacePipeline
from langchain_community.embeddings import HuggingFaceEmbeddings
from transformers import pipeline
from scripts.embed_pages import FAISS_PATH

# --------------
# Logging Setup
# --------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ----------------------------
# LLM Factories
# ----------------------------
def build_local_llm():
    """Build a local HuggingFace model pipeline"""
    logger.info("using local HuggingFace model...")
    generator = pipeline(
        "text-generation",
        model="tiiuae/falcon-7b-instruct", # <- swap model here if needed
        device=-1, # Use CPU instead of GPU to avoid memory issues on my setup with falcon-7b
        dtype="auto", # use fp16 if avl
        max_new_tokens=512
    )
    return HuggingFacePipeline(pipeline=generator)


def get_openai_llm():
    """Import ChatOpenAI dynamically only if needed"""
    try:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
    except ImportError:
        logger.error(
            "langchain_openai not installed. Install it via 'pip install langchain[openai]' "
            "or use the 'local' provider."
        )
        raise


def get_embeddings():
    """Get embeddings model - this should match what is used in embed_pages.py"""
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2" # < -- DEBUG_info! must mirror LLM used in embed_pages.py 
    )


def get_llm(provider: str = None):
    """Return LLM depending on provider or env availability"""
    if provider == "openai" or (provider is None and os.getenv("OPENAI_API_KEY")):
        logger.info("using OpenAI model...")
        return get_openai_llm()
    else:
        return build_local_llm()


# --------------------------------------
# Main Audit Function
# --------------------------------------
def audit_site(query: str, provider: str= None):
    llm = get_llm(provider)

    # get embeddings model (same as used for creating the index)
    embeddings = get_embeddings()

    # load FAISS index with the embeddings model
    logger.info("Loading FAISS index...")
    db = FAISS.load_local(
        FAISS_PATH,
        embeddings,
        allow_dangerous_deserialization=True
    )
    retriever = db.as_retriever()

    # build QA chain
    qa = RetrievalQA.from_chain_type(llm=llm, retriever=retriever)
    result = qa.run(query)
    return result


# --------------------------
# CLI Execution
# --------------------------
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m scripts.audit_site '<your query>' [provider]")
        sys.exit(1)

    query = sys.argv[1]
    provider = sys.argv[2] if len(sys.argv) > 2 else None

    answer = audit_site(query, provider)
    print("\n--- Site Audit Result ---\n")
    print(answer)

# -------------------
# future updates to-do
# -------------------
#->Get embeddings model automatically from embed_pages.py
#->improve CUDA support and swap model, Falcon-7B model VRAM needed: ~14-16GB
#->improve Memory Management for CPU/GPU
#->improve CLI execution and verbose
#->save results to CSV
