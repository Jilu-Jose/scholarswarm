import os
from pathlib import Path

from dotenv import load_dotenv

BASE = Path(__file__).resolve().parent.parent
load_dotenv(BASE / ".env")

# Flexible Cloud LLM support (Groq, OpenAI, Gemini, etc.)
LLM_API_KEY = (
    os.getenv("LLM_API_KEY")
    or os.getenv("GROQ_API_KEY")
    or os.getenv("OPENAI_API_KEY")
    or os.getenv("GEMINI_API_KEY")
    or ""
).strip()

raw_base = os.getenv("LLM_BASE_URL", "").rstrip("/")
raw_model = os.getenv("LLM_MODEL", "").strip()

if os.getenv("GEMINI_API_KEY") and not raw_base:
    LLM_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai"
    LLM_MODEL = raw_model or "gemini-2.0-flash"
elif os.getenv("OPENAI_API_KEY") and not raw_base:
    LLM_BASE_URL = "https://api.openai.com/v1"
    LLM_MODEL = raw_model or "gpt-4o-mini"
else:
    LLM_BASE_URL = raw_base or "https://api.groq.com/openai/v1"
    LLM_MODEL = raw_model or "openai/gpt-oss-120b"


TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

# 1 = fetch official pages live. 0 = offline demo mode (results are labelled "unverified").
LIVE_FETCH = os.getenv("LIVE_FETCH", "1") == "1"
LIVE_DISCOVERY = os.getenv("LIVE_DISCOVERY", "1") == "1"
MAX_CONCURRENCY = int(os.getenv("MAX_CONCURRENCY", "5"))
FETCH_TIMEOUT = float(os.getenv("FETCH_TIMEOUT", "12"))

DATA_DIR = BASE / "data"
RUNS_DIR = BASE / "runs"
FRONTEND_DIR = BASE.parent / "frontend"
