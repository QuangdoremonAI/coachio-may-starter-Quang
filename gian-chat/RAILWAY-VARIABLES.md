# 📋 Variables cho Railway — copy & paste sẵn

Railway → service `gian-chat` → tab **Variables** → **RAW Editor** → dán khối
dưới → điền giá trị sau dấu `=` → **Save / Deploy**.

```dotenv
DEEPSEEK_API_KEY=
TELEGRAM_ALERT_TOKEN=
TELEGRAM_ALERT_CHAT_ID=
TELEGRAM_WEBHOOK_SECRET=
PUBLIC_BASE_URL=
ALLOWED_ORIGINS=
BOT_NAME=Bé Giản
PUBLIC_DOCS=false
ANTHROPIC_API_KEY=
JINA_API_KEY=
```

> `DATABASE_URL` **không cần điền** — gắn Postgres addon là Railway tự bơm vào.

---

## Mỗi key là gì, lấy ở đâu

| Variable | Bắt buộc? | Dùng cho | Lấy ở đâu |
|---|---|---|---|
| `DEEPSEEK_API_KEY` | ✅ | Bộ não chính của bot | platform.deepseek.com → API Keys |
| `TELEGRAM_ALERT_TOKEN` | 🟡 nên có | Bot nhận lead + để anh tiếp quản | @BotFather → `/newbot` — **tạo bot RIÊNG, đừng dùng chung bot Mây** |
| `TELEGRAM_ALERT_CHAT_ID` | 🟡 nên có | Group nhận brief | Tạo group → thêm bot vào → @Getmyid_bot lấy ID group (số âm) |
| `TELEGRAM_WEBHOOK_SECRET` | 🟡 nên có | Chặn người lạ giả webhook | Tự gõ một chuỗi ngẫu nhiên dài |
| `PUBLIC_BASE_URL` | 🟡 nên có | Để tự trỏ webhook Telegram | Domain Railway cấp, vd `https://gian-chat.up.railway.app` |
| `ALLOWED_ORIGINS` | ✅ khi lên thật | Chỉ web của anh gọi được API | Domain web, vd `https://anhquangdongian.vn` |
| `BOT_NAME` | ⬜ | Tên hiện trên khung chat | Mặc định "Bé Giản" |
| `PUBLIC_DOCS` | ✅ | **Phải là `false` khi lên thật** | — |
| `ANTHROPIC_API_KEY` | ⬜ | Tầng "khó" — Claude Haiku cho câu về tiền | console.anthropic.com |
| `JINA_API_KEY` | ⬜ | Tìm tài liệu bằng ngữ nghĩa (chính xác hơn) | jina.ai |

---

## Lấy `TELEGRAM_ALERT_CHAT_ID` của group

1. Tạo group Telegram, đặt tên kiểu "Lead Bé Giản".
2. Thêm bot vừa tạo vào group, cho quyền đọc tin.
3. Thêm **@Getmyid_bot** vào group → nó in ra ID (số **âm**, vd `-1002345678`).
4. Dán số đó vào `TELEGRAM_ALERT_CHAT_ID`, rồi kick @Getmyid_bot ra.

---

## Kiểm sau khi deploy

```bash
curl https://<domain>/healthz        # phải ra {"ok":true,...}
curl -o /dev/null -w "%{http_code}" https://<domain>/openapi.json   # phải là 404
```

`healthz` trả về `"chunks": 0` nghĩa là **bot chưa đọc được knowledge base nào** —
kiểm lại `kb/` đã commit chưa, hoặc các file còn đầy `<<< ĐIỀN >>>`.

---

## Lưu ý

- Key là bí mật: **chỉ** đặt trong Railway Variables, không commit vào GitHub.
- Sửa nội dung `kb/` → commit → Railway tự deploy → bot học ngay, không cần
  làm gì thêm.
- Đổi ưu đãi hoặc lịch khai giảng thì nhớ sửa `kb/02-hoc-phi-lich/` rồi deploy,
  nếu không bot vẫn nói theo thông tin cũ.
