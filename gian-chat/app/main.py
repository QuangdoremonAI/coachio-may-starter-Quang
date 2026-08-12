"""Bé Giản — chatbot web của Anh Quang đơn giản.

Chạy local:   uvicorn app.main:app --reload
Chạy Railway: Dockerfile lo hết.
"""
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from app import ratelimit
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



@app.middleware("http")
async def _rate_limit(request: Request, call_next):
    try:
        ratelimit.check(request)
    except HTTPException as e:
        return JSONResponse({"detail": e.detail}, status_code=e.status_code)
    return await call_next(request)


app.include_router(chat.router)
app.include_router(history.router)
app.include_router(agent.router)
app.include_router(lead.router)


@app.get("/healthz")
async def healthz():
    return {"ok": True, "bot": BOT_NAME, "kb": rag.stats()}


@app.get("/widget.js")
async def widget():
    """Ưu tiên bản đã minify. Bản nguồn còn nguyên comment giải thích cách
    hệ hoạt động — đúng thứ MONA để lộ. Chạy scripts/build_widget.sh để tạo
    widget.min.js; có file đó thì bản nguồn không bao giờ ra ngoài."""
    minified = STATIC_DIR / "widget.min.js"
    path = minified if minified.exists() else STATIC_DIR / "widget.js"
    if not minified.exists():
        log.warning("Đang serve widget.js CHƯA MINIFY — chạy scripts/build_widget.sh")
    return FileResponse(
        path,
        media_type="application/javascript",
        headers={"Cache-Control": "public, max-age=300"},
    )


@app.get("/test")
async def test_page():
    """Trang thử. Chỉ mở khi PUBLIC_DOCS=true — lên thật thì tắt cùng /docs."""
    if not PUBLIC_DOCS:
        raise HTTPException(status_code=404)
    return FileResponse(STATIC_DIR / "test.html", media_type="text/html")
