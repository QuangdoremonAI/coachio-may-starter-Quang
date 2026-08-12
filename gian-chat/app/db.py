"""Kết nối DB. Dùng SQLAlchemy đồng bộ + asyncio.to_thread cho gọn đầu.

Lưu lượng dự kiến ~1.000 hội thoại/tháng nên không cần async driver.
Mọi hàm chạm DB đều được gọi qua `run_db()` để khỏi chặn event loop.
"""
import asyncio
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable

from sqlalchemy import create_engine
from sqlalchemy.orm import Session as OrmSession
from sqlalchemy.orm import sessionmaker

from app.config import DATABASE_URL
from app.models import Base

if DATABASE_URL.startswith("sqlite"):
    Path(DATABASE_URL.split("///")[-1]).parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=5, max_overflow=5)

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def init_db() -> None:
    Base.metadata.create_all(engine)


@contextmanager
def db_session():
    s: OrmSession = SessionLocal()
    try:
        yield s
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


async def run_db(fn: Callable[..., Any], *args, **kwargs) -> Any:
    """Chạy hàm chạm DB trong threadpool. fn nhận session làm tham số đầu."""

    def _wrapped():
        with db_session() as s:
            return fn(s, *args, **kwargs)

    return await asyncio.to_thread(_wrapped)
