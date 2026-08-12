# Bé Giản — chatbot web của Anh Quang đơn giản.
# Deploy: Railway (hoặc VPS bất kỳ chạy được Docker).
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

# kb/ đi kèm image — đổi nội dung KB thì deploy lại là bot học ngay.
COPY app ./app
COPY kb ./kb
COPY scripts ./scripts

# SQLite fallback ghi vào đây (Railway: gắn Volume vào /app/data cho khỏi mất)
RUN mkdir -p /app/data

EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
