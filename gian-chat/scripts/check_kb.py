"""Kiểm tra knowledge base trước khi deploy.

Chạy:  python scripts/check_kb.py

Bắt các lỗi hay gặp nhất:
  - file còn chỗ <<< ĐIỀN >>> chưa viết
  - thiếu metadata đầu file
  - đoạn dài quá (bot sẽ trả lời cụt)
  - bảng giá trống (guard sẽ chặn MỌI con số bot nói ra)
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.guard import load_price_whitelist  # noqa: E402
from app.core.rag import load_kb  # noqa: E402
from app.config import KB_DIR  # noqa: E402

RED, YEL, GRN, OFF = "\033[31m", "\033[33m", "\033[32m", "\033[0m"


def main() -> int:
    errors, warns = [], []

    if not KB_DIR.exists():
        print(f"{RED}✗ Không thấy thư mục kb/ tại {KB_DIR}{OFF}")
        return 1

    files = [p for p in sorted(KB_DIR.rglob("*.md"))
             if not p.name.upper().startswith("README")]
    if not files:
        errors.append("kb/ chưa có file .md nào")

    for p in files:
        rel = p.relative_to(KB_DIR)
        raw = p.read_text(encoding="utf-8")

        if "<<<" in raw:
            n = raw.count("<<<")
            warns.append(f"{rel}: còn {n} chỗ <<< ĐIỀN >>> chưa viết")

        if not raw.startswith("---"):
            warns.append(f"{rel}: thiếu metadata đầu file (chu_de / tra_loi_cho / cap_nhat)")
        else:
            head = raw[:raw.find("\n---", 3) + 1] if "\n---" in raw[3:] else ""
            for key in ("chu_de", "tra_loi_cho", "cap_nhat"):
                if key not in head:
                    warns.append(f"{rel}: metadata thiếu `{key}`")

        body_words = len(re.sub(r"^---.*?---", "", raw, flags=re.S).split())
        if body_words < 30:
            warns.append(f"{rel}: quá ngắn ({body_words} từ) — bot khó trả lời từ đây")

    chunks = load_kb()
    prices = load_price_whitelist()

    print(f"\n📚 {len(files)} file · {len(chunks)} đoạn · {len(prices)} con số tiền hợp lệ\n")

    if not prices:
        errors.append(
            "kb/ chưa có con số tiền nào → guard sẽ CHẶN mọi con số bot nói ra. "
            "Điền kb/02-hoc-phi-lich/hoc-phi.md trước."
        )

    long_chunks = [c for c in chunks if len(c.text.split()) > 400]
    if long_chunks:
        warns.append(f"{len(long_chunks)} đoạn dài hơn 400 từ — cân nhắc cắt bằng heading ##")

    for w in warns:
        print(f"{YEL}⚠ {w}{OFF}")
    for e in errors:
        print(f"{RED}✗ {e}{OFF}")

    if not errors and not warns:
        print(f"{GRN}✓ Knowledge base sạch, sẵn sàng deploy{OFF}")
    elif not errors:
        print(f"\n{GRN}✓ Không có lỗi chặn deploy{OFF} (còn {len(warns)} cảnh báo)")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
