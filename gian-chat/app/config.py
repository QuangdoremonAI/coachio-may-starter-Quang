"""Cấu hình đọc từ biến môi trường. Không hardcode key ở bất cứ đâu khác."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


# ─── Bot ──────────────────────────────────────────────────────────────
BOT_NAME = os.getenv("BOT_NAME", "Bé Giản")
KB_DIR = Path(os.getenv("KB_DIR", BASE_DIR / "kb"))

# ─── LLM ──────────────────────────────────────────────────────────────
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "").strip()
DEEPSEEK_BASE = "https://api.deepseek.com/v1"
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
ANTHROPIC_BASE = "https://api.anthropic.com/v1"
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")

LLM_TIMEOUT_S = float(os.getenv("LLM_TIMEOUT_S", "45"))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "700"))

# ─── Embedding (tuỳ chọn — không có thì RAG chạy bằng từ khoá) ─────────
JINA_API_KEY = os.getenv("JINA_API_KEY", "").strip()
JINA_MODEL = os.getenv("JINA_MODEL", "jina-embeddings-v3")

# ─── Database ─────────────────────────────────────────────────────────
# Railway Postgres cấp DATABASE_URL dạng postgres:// — SQLAlchemy cần postgresql+psycopg://
_raw_db = os.getenv("DATABASE_URL", "").strip()
if _raw_db.startswith("postgres://"):
    _raw_db = _raw_db.replace("postgres://", "postgresql+psycopg://", 1)
elif _raw_db.startswith("postgresql://"):
    _raw_db = _raw_db.replace("postgresql://", "postgresql+psycopg://", 1)
DATABASE_URL = _raw_db or f"sqlite:///{BASE_DIR / 'data' / 'gian.db'}"

# ─── Telegram (nhận lead + tiếp quản) ─────────────────────────────────
TELEGRAM_ALERT_TOKEN = os.getenv("TELEGRAM_ALERT_TOKEN", "").strip()
TELEGRAM_ALERT_CHAT_ID = os.getenv("TELEGRAM_ALERT_CHAT_ID", "").strip()
TELEGRAM_WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET", "gian-hook").strip()

# ─── Web ──────────────────────────────────────────────────────────────
ALLOWED_ORIGINS = [
    o.strip() for o in os.getenv("ALLOWED_ORIGINS", "*").split(",") if o.strip()
]
PUBLIC_DOCS = _bool("PUBLIC_DOCS", False)

# ─── Hội thoại ────────────────────────────────────────────────────────
HISTORY_TURNS = int(os.getenv("HISTORY_TURNS", "20"))   # số tin nạp lại vào prompt
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "6"))            # số đoạn KB đưa vào prompt
MAX_WORDS_PER_MSG = int(os.getenv("MAX_WORDS_PER_MSG", "45"))
