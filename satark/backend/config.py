import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"), override=True)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-2.5-flash"
CHROMA_PERSIST_DIR = os.path.join(os.path.dirname(__file__), "vectorstore", "chroma_db")
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
RAG_TOP_K = 2
MAX_RESPONSE_TOKENS = 600
