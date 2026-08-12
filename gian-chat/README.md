# 🌿 Bé Giản — chatbot web của Anh Quang đơn giản

Trợ lý AI trả lời khách trên website 24/7: hiểu khách đang mắc ở đâu, điều hướng
đúng chương trình, và chuyển sang người thật khi cần.

Thiết kế học từ hệ chatbot của MONA (xem `../CHATBOT-WEB-AQUANG.md` để biết
nghiên cứu đầy đủ), nhưng **đổi trục từ "ép chốt" sang "sàng lọc đúng người"**.

---

## Chạy thử trong 5 phút (máy của anh)

```bash
cd gian-chat
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

cp .env.example .env          # rồi mở ra điền DEEPSEEK_API_KEY

.venv/bin/python scripts/check_kb.py      # kiểm knowledge base
.venv/bin/python scripts/smoke_test.py    # chạy thử toàn luồng, KHÔNG tốn tiền

.venv/bin/python -m uvicorn app.main:app --reload
```

Mở **http://localhost:8000/test** → bong bóng chat hiện góc dưới phải.

> Trang `/test` chỉ mở khi `PUBLIC_DOCS=true` (mặc định trong `.env.example`).
> Lên thật thì đặt `false`, nó tự 404 cùng với `/docs`.

> `smoke_test.py` thay model thật bằng model giả nên chạy bao nhiêu lần cũng
> không mất tiền. Chạy nó **sau mỗi lần sửa code**, trước khi deploy.

Sửa `widget.js` xong thì build lại bản minify:

```bash
bash scripts/build_widget.sh
```

---

## Lên Railway

1. Push repo lên GitHub.
2. Railway → **New Project** → **Deploy from GitHub repo** → chọn repo này.
3. **Settings → Root Directory** → gõ `gian-chat`.
4. Railway tự thấy `Dockerfile` và build.
5. **New → Database → PostgreSQL** (Railway tự gắn `DATABASE_URL`).
6. Tab **Variables** → dán khối trong `RAILWAY-VARIABLES.md`.
7. **Settings → Networking → Generate Domain**.
8. Xong. Kiểm: mở `https://<domain>/healthz` phải ra `{"ok":true,...}`.

Không gắn Postgres cũng chạy được (tự dùng SQLite), nhưng Railway xoá container
là mất hết hội thoại. Gắn Postgres đi, miễn phí ở mức này.

---

## Nhúng lên website

```html
<script src="https://<domain>/widget.js" defer></script>
```

Tuỳ biến:

```html
<script src="https://<domain>/widget.js"
        data-bot-name="Bé Giản"
        data-accent="#2E7D5B"
        data-avatar="https://<domain>/static/be-gian.png"
        data-zalo="https://zalo.me/..."
        data-position="bottom-right"
        defer></script>
```

Gắn nút bất kỳ trên site vào chat:

```html
<button onclick="Gian.open('Em ơi CCSC học bao lâu?')">Hỏi Bé Giản</button>
<button onclick="Gian.openCampaign('ccsc-t8','Cho em hỏi khoá sắp khai giảng')">
  Tìm hiểu khoá CCSC
</button>
```

---

## Cấu trúc

```
gian-chat/
├── app/
│   ├── main.py            FastAPI, bật/tắt docs, serve widget
│   ├── config.py          mọi biến môi trường
│   ├── models.py          4 bảng: sessions · messages · leads
│   ├── store.py           mọi câu query gom về đây
│   ├── routes/
│   │   ├── chat.py        ⭐ POST /chat — trái tim, luồng SSE
│   │   ├── history.py     khôi phục hội thoại cũ
│   │   ├── agent.py       tiếp quản từ Telegram + agent-pull
│   │   └── lead.py        form để lại số
│   ├── core/
│   │   ├── prompt.py      ⭐ system prompt + tin ẩn [CONTEXT]
│   │   ├── rag.py         tìm đoạn tài liệu khớp câu hỏi
│   │   ├── llm.py         router DeepSeek ↔ Claude Haiku
│   │   ├── guard.py       ⭐ 5 lằn ranh cứng
│   │   ├── splitter.py    cắt thành 2-3 tin + gõ giả
│   │   ├── tagger.py      tách [TAG] / [LEAD] / [CHUYEN_NGUOI]
│   │   └── telegram.py    brief lead + nhận anh gõ trả lời
│   └── static/
│       ├── widget.js      widget nhúng (⚠️ minify trước khi lên thật)
│       └── test.html      trang thử
├── kb/                    ⭐ BỘ NÃO — đọc kb/README.md
└── scripts/
    ├── check_kb.py        kiểm knowledge base
    └── smoke_test.py      chạy thử toàn luồng, không tốn tiền
```

Ba file có ⭐ là chỗ anh sẽ sửa nhiều nhất. `kb/` là chỗ sửa **nhiều nhất trong
những chỗ nhiều nhất**.

---

## Luồng một tin nhắn

```
Khách gõ
  → widget gom ngữ cảnh (trang đang xem, hành trình, nguồn quảng cáo)
  → POST /chat
  → chặn câu moi prompt
  → nếu người thật đang tiếp quản → bot IM LẶNG
  → nạp lịch sử + tìm đoạn KB khớp
  → ghép prompt → gọi model (DeepSeek hoặc Haiku)
  → tách dòng điều khiển [TAG]/[LEAD]
  → lọc: giá bịa? hứa hẹn? ngoài phạm vi?
  → cắt thành 2-3 tin, nghỉ giữa các tin
  → SSE: session → typing → message → tag → done
  → lead nóng → brief sang Telegram
```

---

## Người thật tiếp quản

1. Bot phát hiện lead nóng → đẩy brief vào group Telegram.
2. Anh **reply thẳng vào tin brief** → khách thấy ngay trong khung chat,
   vẫn tên và avatar Bé Giản.
3. Từ lúc đó **bot im hẳn**, không nói chen vào.
4. Xong việc, reply `/tra` → trả quyền lại cho bot.

---

## Bot KHÔNG THỂ bịa giá

`kb/02-hoc-phi-lich/hoc-phi.md` vừa là tài liệu vừa là **danh sách trắng**.
Code quét file đó lấy mọi con số tiền; bot nói ra số nào không có trong đó thì
bị chặn ngay, thay bằng "để em gửi bảng giá chính thức".

Chặn ở **code**, không phải ở prompt — model lú cũng không lọt.

Hệ quả: file đó trống thì bot không nói được con số nào. `check_kb.py` sẽ báo đỏ.

---

## 🔒 Chống rò rỉ

Toàn bộ bài phân tích hệ MONA lấy được trong 10 phút chỉ nhờ **hai chỗ họ để hở**:
`/openapi.json` public, và `widget.js` ship không minify với đầy comment nội bộ —
lộ cả tên khách hàng lẫn số liệu lead thật. Hệ này bịt sẵn đúng những chỗ đó,
và `smoke_test.py` kiểm lại mỗi lần chạy.

| Chỗ hở | Ở đây xử lý thế nào |
|---|---|
| `/openapi.json`, `/docs` | Tắt mặc định. `PUBLIC_DOCS=false` là 404. |
| Trang thử `/test` | Cũng tắt theo `PUBLIC_DOCS` — không để hở trang debug. |
| `widget.js` lộ comment | Server **ưu tiên `widget.min.js`**. Build script tự kiểm: lọt `[CONTEXT]` hoặc sót comment là fail. |
| Prompt nằm ở client | Nội dung `[CONTEXT]` để **hết ở server** (`core/prompt.py`). Widget chỉ gửi token kiểu `/_nudge_` — đọc bản minify không suy ra được prompt. |
| Đọc trộm hội thoại người khác | `/history` nhận `visitor_id` trần, nên id sinh bằng `crypto.randomUUID` (122 bit). Không đoán được, khác `Math.random()` chỉ ~40 bit. |
| Lỗi lộ nội bộ | Event `error` chỉ trả `upstream_error`. Chi tiết vào log server. |
| Đốt tiền API / ngập Telegram | Rate limit theo IP: `/chat` 20 lượt/phút, `/lead` 5 lượt/5 phút. |

Còn một chỗ **chưa bịt**, nói rõ để anh biết mà quyết: `/history` và
`/chat/agent-pull` chưa có xác thực — ai cầm được `visitor_id` hoặc
`session_id` của người khác thì đọc được hội thoại của họ. Hiện chỉ dựa vào
việc id không đoán nổi. Muốn chặt hơn thì ký id bằng HMAC và kiểm chữ ký;
ở mức một site tư vấn thì em thấy chưa cần, nhưng đây là lựa chọn của anh.

---

## ⚠️ Trước khi cho chạy công khai

- [ ] `PUBLIC_DOCS=false` — kiểm `curl https://<domain>/openapi.json` ra **404**
- [ ] `curl https://<domain>/test` cũng phải ra **404**
- [ ] `ALLOWED_ORIGINS` điền đúng domain, không để `*`
- [ ] `bash scripts/build_widget.sh` — có `widget.min.js` mới hơn `widget.js`
- [ ] `TELEGRAM_WEBHOOK_SECRET` đổi thành chuỗi ngẫu nhiên
- [ ] `python scripts/smoke_test.py` xanh hết, kể cả mục 🔒
- [ ] `check_kb.py` không còn báo đỏ
- [ ] Chạy hết checklist nghiệm thu trong `../CHATBOT-WEB-AQUANG.md` (mục B10)

---

## Chi phí vận hành

| Khoản | Tháng |
|---|---|
| Railway (service + Postgres) | ~120k–250k |
| DeepSeek (~80% lượt) | ~100k–300k |
| Claude Haiku (~20% lượt) | ~200k–500k |
| **Tổng** | **~500k–1.1tr** cho 1.000 hội thoại |

Không có `ANTHROPIC_API_KEY` thì mọi câu chạy DeepSeek — rẻ hơn nữa, nhưng câu
về tiền sẽ kém tinh.
