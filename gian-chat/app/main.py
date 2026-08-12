"""Bé Giản — chatbot web của Anh Quang đơn giản.

Chạy local:   uvicorn app.main:app --reload
Chạy Railway: Dockerfile lo hết.
"""
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse

from app.config import ALLOWED_ORIGINS, BOT_NAME, PUBLIC_DOCS, TELEGRAM_WEBHOOK_SECRET
from app.core import guard, rag, telegram
from app.db import init_db
from app.routes import agent, chat, history, lead

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
log = logging.getLogger("gian")

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    await rag.warmup()          # nạp kb/ vào RAM + tính embedding
    guard.warmup()              # đọc bảng giá hợp lệ từ kb/
    base = os.getenv("PUBLIC_BASE_URL", "").strip()
    if base:
        await telegram.set_webhook(base, TELEGRAM_WEBHOOK_SECRET)
    log.info("%s sẵn sàng · KB: %s", BOT_NAME, rag.stats())
    yield


app = FastAPI(
    title=f"{BOT_NAME} — trợ lý Anh Quang đơn giản",
    lifespan=lifespan,
    # LÊN THẬT phải tắt. MONA để public và lộ sạch 42 endpoint.
    docs_url="/docs" if PUBLIC_DOCS else None,
    redoc_url=None,
    openapi_url="/openapi.json" if PUBLIC_DOCS else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(history.router)
app.include_router(agent.router)
app.include_router(lead.router)


@app.get("/healthz")
async def healthz():
    return {"ok": True, "bot": BOT_NAME, "kb": rag.stats()}


@app.get("/widget.js")
async def widget():
    """Serve widget cho web nhúng. Nhớ minify trước khi lên thật."""
    return FileResponse(
        STATIC_DIR / "widget.js",
        media_type="application/javascript",
        headers={"Cache-Control": "public, max-age=300"},
    )


@app.get("/test", response_class=PlainTextResponse)
async def test_page():
    """Trang thử nhanh — mở /test là chat được, khỏi cần website."""
    return FileResponse(STATIC_DIR / "test.html", media_type="text/html")
