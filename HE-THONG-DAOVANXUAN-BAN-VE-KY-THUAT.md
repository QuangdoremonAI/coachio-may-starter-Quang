# Hệ thống daovanxuan.com — Bản vẽ kỹ thuật để thi công lại

> Tài liệu này tập trung vào **HỆ THỐNG**: máy móc, luồng dữ liệu, API, schema, quy trình vận hành.
> Phần công thức bán hàng/copywriting nằm ở `PHAN-TICH-DOI-THU-DAOVANXUAN.md`.
> Dữ liệu quét: 12/08/2026 — mã nguồn công khai, DNS, HTTP headers, endpoint công khai.
> Không dò quét xâm nhập, không thử endpoint riêng tư.

---

## PHẦN 0 — Sơ đồ toàn hệ

Họ không có "một hệ thống". Họ có **sáu hệ thống nối nhau**, mỗi hệ một nhiệm vụ:

```
┌──────────────────────────────────────────────────────────────────────┐
│ HỆ 1 — THU HÚT      Facebook Ads → LP                                │
│ HỆ 2 — CHUYỂN ĐỔI   LP tĩnh 26 khối + Pixel + đo lường               │
│ HỆ 3 — GIAO DỊCH    form → n8n → QR → SePay → đối soát tự động       │
│ HỆ 4 — GIAO HÀNG    nhóm Zalo → buổi live 4h → khách lắp chuỗi       │
│ HỆ 5 — SẢN PHẨM     "Cỗ Máy" = n8n + Sheets + Claude + FB Graph      │
│ HỆ 6 — GIỮ & BÁN    kèm bù thứ 7 → PRELA Cloud 686k/th → 5 buổi     │
└──────────────────────────────────────────────────────────────────────┘
```

**Điểm mấu chốt:** HỆ 5 (sản phẩm khách nhận) và HỆ 3 (máy bán hàng của họ) **dùng chung một công nghệ lõi: n8n**. Họ dạy đúng cái họ đang dùng. Đó là lý do họ dựng nhanh, sửa nhanh, và demo được — chứ không phải dạy lý thuyết.

### Hạ tầng thật (đã xác minh)

| Thành phần | Thực tế |
|---|---|
| Landing page | `112.78.2.37` · **LiteSpeed** · hosting chia sẻ Việt Nam · file HTML tĩnh 185KB · `last-modified` 11/08/2026 (sửa liên tục) |
| n8n | `n8n2.daovanxuan.com` → `194.233.75.226` · sau **Caddy** reverse proxy · VPS riêng |
| Thanh toán | **SePay** webhook + **VietQR** image API · MB Bank `875676875` |
| Đo lường | Meta Pixel `1089016496553404` + Facebook domain verification |
| Kênh khách | **Zalo** (cá nhân `0946728686` + nhóm học viên) — không dùng email |

Tên host `n8n2` cho thấy có ít nhất một instance n8n trước đó. Họ tách LP (hosting rẻ, tĩnh, nhanh) khỏi backend (VPS, n8n) — đúng kiến trúc: **trang bán hàng không được chết vì backend chết**.

---

## PHẦN 1 — HỆ 5: Tái dựng "Cỗ Máy Sản Xuất Nội Dung"

Đây là sản phẩm họ bán 399k. Từ khối 09 "Dưới nắp capo", họ tự công bố 6 bộ phận. Dưới đây là bản dựng lại đầy đủ, đủ để thi công.

### 1.1 Kiến trúc

```
┌─ Google Sheets (bộ nhớ) ────────────┐
│  GIONG_VAN · DE_TAI · HOOK          │
│  LICH · NHAT_KY                     │
└──────────────┬──────────────────────┘
               │ đọc/ghi
        ┌──────▼───────────────────────────────────┐
Cron ──▶│  n8n workflow "Đăng bài"                 │
        │  1. Kiểm lịch    2. Bốc đề tài + hook    │
        │  3. Đọc giọng    4. Gọi Claude           │
        │  5. Duyệt/tự động 6. Đăng   7. Ghi log   │
        └──────┬──────────────────┬────────────────┘
               │                  │
      Claude API              Facebook Graph API
   (khóa của khách)          (Page Access Token)
```

### 1.2 Schema Google Sheets — 5 tab

**Tab `GIONG_VAN`** (bộ nhớ giọng văn — lý do bài không "giống văn AI")

| Cột | Nội dung |
|---|---|
| `loai` | `mau_bai` \| `quy_tac` |
| `noi_dung` | Nguyên văn bài khách đã viết, hoặc một quy tắc |
| `ghi_chu` | — |

Quy tắc nên có sẵn ~12 dòng: độ dài bài, cách xuống dòng, xưng hô (`mình/bạn`, `anh/chị`, `em/thầy`), emoji dùng hay không, có CTA cuối bài không, cấm từ nào, mở bài kiểu gì, kết bài kiểu gì.

**Tab `DE_TAI`** (365 dòng)

| `id` | `nhom` | `de_tai` | `goi_y` | `da_dung_ngay` | `so_lan` |
|---|---|---|---|---|---|
| 1 | Chuyên môn | Sai lầm số 1 khi… | Kể 1 ca thật + bài học | | 0 |

**Tab `HOOK`** (100 dòng)

| `id` | `nhom_tep` | `mau_hook` | `da_dung_ngay` |
|---|---|---|---|

**Tab `LICH`** (cấu hình — khách tự sửa, không cần đụng n8n)

| `khoa` | `gia_tri` |
|---|---|
| `trang_thai` | `chay` \| `tam_dung` |
| `gio_dang` | `07:00,19:30` |
| `ngay_trong_tuan` | `2,3,4,5,6,7` |
| `so_bai_moi_ngay` | `1` |
| `che_do` | `tu_dong` \| `duyet_tay` |
| `page_id` | `123456789` |

**Tab `NHAT_KY`** (sổ nhật ký — khối 09 mục 6)

| `thoi_gian` | `de_tai_id` | `hook_id` | `noi_dung` | `fb_post_id` | `trang_thai` | `loi` | `tokens_in` | `tokens_out` | `chi_phi_vnd` |
|---|---|---|---|---|---|---|---|---|---|

> Hai cột token + chi phí là **thứ họ không có** và bạn nên thêm: khách mở ra thấy đúng số tiền đã tiêu → diệt sạch nghi ngờ "dùng lâu có tốn không". Đây là nâng cấp rẻ mà mạnh.

### 1.3 Chuỗi n8n — từng node

```
[1] Schedule Trigger — cron theo LICH.gio_dang
     ↓
[2] Google Sheets: Read  LICH
     ↓
[3] IF  trang_thai = "chay"  AND  hôm nay ∈ ngay_trong_tuan
     ↓ true
[4] Google Sheets: Read  DE_TAI   → Filter da_dung_ngay rỗng → Random 1
[5] Google Sheets: Read  HOOK     → Filter da_dung_ngay rỗng → Random 1
[6] Google Sheets: Read  GIONG_VAN → gộp mẫu bài + quy tắc
     ↓
[7] HTTP Request → Claude API   (chi tiết ở 1.4)
     ↓
[8] IF  che_do = "duyet_tay"
     ├─ true  → gửi Telegram/Zalo cho khách → chờ nút Duyệt → [9]
     └─ false → [9]
     ↓
[9] HTTP Request → Facebook Graph API  (chi tiết ở 1.5)
     ↓
[10] Google Sheets: Append NHAT_KY  (+ token, + chi phí)
[11] Google Sheets: Update DE_TAI/HOOK  đánh dấu da_dung_ngay
     ↓
[Error branch] → Append NHAT_KY (trang_thai = "loi") + báo Telegram/Zalo chủ page
```

**Ba chi tiết quyết định chuỗi sống hay chết:**

1. **Đánh dấu đã dùng SAU khi đăng thành công**, không phải trước. Đăng lỗi mà đã đánh dấu thì mất đề tài vĩnh viễn.
2. **Error branch bắt buộc.** Không có nó, chuỗi chết âm thầm và khách chỉ phát hiện sau 2 tuần page trống — đó là lúc họ đòi hoàn tiền.
3. **Hết đề tài phải quay vòng**: khi tất cả `da_dung_ngay` đã điền → xoá sạch cột đó và chạy lại từ đầu (365 ngày = tròn 1 năm, đúng như họ quảng cáo).

### 1.4 Gọi Claude API — shape chính xác

`POST https://api.anthropic.com/v1/messages`

```
x-api-key: <khóa của khách>
anthropic-version: 2023-06-01
content-type: application/json
```

```json
{
  "model": "claude-opus-5",
  "max_tokens": 2000,
  "system": "Bạn viết bài Facebook thay cho một chuyên gia. Viết ĐÚNG giọng của họ.\n\n## Quy tắc giọng văn\n{{quy_tac}}\n\n## Mẫu bài họ đã viết\n{{mau_bai_1}}\n---\n{{mau_bai_2}}\n---\n{{mau_bai_3}}\n\nChỉ trả về nội dung bài đăng. Không thêm lời dẫn, không giải thích, không tiêu đề.",
  "messages": [
    { "role": "user",
      "content": "Đề tài: {{de_tai}}\nGợi ý triển khai: {{goi_y}}\nCâu mở đầu bắt buộc dùng: {{mau_hook}}" }
  ]
}
```

Đọc kết quả: `response.content[]` → lấy block `type == "text"` → `.text`.
Đọc chi phí: `response.usage.input_tokens` / `.output_tokens` → ghi vào `NHAT_KY`.

**Ba lưu ý API mà một chuỗi n8n hay vấp:**

- **Duyệt `content` theo `type`, đừng lấy cứng `content[0].text`.** Trên các model đời mới thinking bật mặc định, block đầu có thể là `thinking` → lấy `content[0]` sẽ ra rỗng.
- **`max_tokens` là trần cho *cả* thinking lẫn bài viết.** Đặt 2000 cho một bài FB là rộng rãi; đặt 500 thì có ngày bị cắt giữa chừng.
- **Không cần prompt caching cho 1 bài/ngày.** Cache chỉ sống 5 phút — cron mỗi ngày một lần thì không bao giờ trúng cache. Caching chỉ đáng làm nếu bạn sinh cả tháng bài trong một lần chạy (xem 1.7).

### 1.5 Đăng lên Fanpage — Facebook Graph API

`POST https://graph.facebook.com/v21.0/{page_id}/feed`

```
message=<nội dung bài>
access_token=<Page Access Token>
```

Trả về `{"id": "{page_id}_{post_id}"}` → ghi vào `NHAT_KY.fb_post_id`.

**Đây chính là "bước hay lỗi nhất" mà họ tự thừa nhận trên trang.** Vì sao:

| Cạm bẫy | Xử lý |
|---|---|
| Quyền thiếu | Cần `pages_manage_posts` + `pages_read_engagement`; App phải qua App Review nếu dùng cho người ngoài |
| Token hết hạn | User token ngắn hạn (~1h) → đổi sang long-lived user token (~60 ngày) → **lấy Page token từ token dài hạn đó thì Page token không hết hạn** |
| Đăng nhầm nơi | `page_id` sai → bài lên trang khác. Bắt buộc hiện tên page ra cho khách xác nhận (đây chính là "chiến thắng đầu tiên" phút 0:35 của họ) |
| Facebook đổi API | Version `v21.0` sẽ bị khai tử theo lịch ~2 năm. Phải có người theo dõi → **đây là lý do tồn tại của gói vận hành hộ 686k/tháng** |

> Nói thẳng về mô hình kinh doanh: **rủi ro Facebook API chính là thứ sinh ra doanh thu lặp lại của họ.** Chuỗi càng dễ gãy vì bên thứ ba, gói "vận hành hộ" càng dễ bán.

### 1.6 Kiểm chứng lời hứa chi phí của họ

Họ công bố: **290đ/bài · ~8.600đ/tháng · nạp 130k dùng hơn 1 năm.**

Ước lượng đầu vào thực tế: giọng văn (3 bài mẫu + quy tắc) + đề tài + hook ≈ **2.500 token vào**; một bài FB tiếng Việt ~300 từ ≈ **700 token ra** (tiếng Việt tốn token hơn tiếng Anh đáng kể).

Theo bảng giá Anthropic hiện hành (USD/1 triệu token), tỷ giá tham chiếu ~26.000đ/USD:

| Model | Vào $/M | Ra $/M | 1 bài | ≈ VNĐ/bài | ≈ VNĐ/tháng (30 bài) |
|---|---|---|---|---|---|
| Claude Opus 5 | 5,00 | 25,00 | $0,0300 | ~780đ | ~23.400đ |
| Claude Sonnet 5 | 3,00 | 15,00 | $0,0180 | ~470đ | ~14.000đ |
| Claude Haiku 4.5 | 1,00 | 5,00 | $0,0060 | ~160đ | ~4.700đ |

**Kết luận: con số 290đ/bài của họ nằm gọn giữa Haiku 4.5 và Sonnet 5 — hợp lý, không thổi phồng.** Nó ứng với model hạng Haiku với prompt lớn hơn ước tính, hoặc hạng Sonnet với prompt gọn hơn. Còn "$5 ≈ 130k dùng hơn một năm": $5 ÷ $0,011 ≈ 450 bài ≈ 15 tháng — **đúng**.

Đây là điểm đáng học nhất về mặt kỹ thuật: **họ đưa ra một con số nhỏ, cụ thể, và kiểm chứng được.** Bạn nên làm y hệt — và làm tốt hơn bằng cách ghi chi phí thật vào `NHAT_KY` để khách tự đối chiếu.

### 1.7 Ba chỗ bạn làm tốt hơn họ được ngay

1. **Sinh bài theo lô + Batch API.** Nội dung đăng bài không nhạy latency. Gom 30 bài chạy một lần qua Message Batches → **giảm 50% chi phí token**, và lúc đó prompt caching mới có tác dụng (khối giọng văn dùng lại 30 lần). Chuỗi của họ chạy từng bài một → trả giá đầy đủ mỗi lần.
2. **Ghi token + chi phí vào nhật ký.** Biến "chi phí" từ nỗi lo mơ hồ thành con số khách tự nhìn thấy.
3. **Hàng rào chất lượng trước khi đăng.** Thêm một node kiểm: bài có rỗng không, có quá ngắn không, có chứa `<thinking>` hay lời dẫn kiểu "Đây là bài viết…" không. Bắt được thì viết lại một lần, vẫn hỏng thì chuyển sang duyệt tay và báo chủ page. Chuỗi của họ không có lớp này — bài lỗi lên thẳng page thật.

---

## PHẦN 2 — HỆ 3: Máy nhận đơn và đối soát tiền

Đây là phần khiến họ vận hành được một mình mà không cần nhân viên trực đơn.

### 2.1 Luồng đầy đủ

```
Khách điền form (Tên + SĐT)
   │  JS sinh mã đơn tại trình duyệt: PRL + 4 số cuối SĐT + 3 chữ ngẫu nhiên
   │  Nội dung CK = "PRELA " + mã đơn
   ▼
POST n8n2.../webhook/order-form   ← CORS bật đúng domain
   │  n8n: ghi đơn (trạng thái = cho_thanh_toan), giữ chỗ 30 phút
   ▼
Trang hiện QR ngay tại chỗ (không nhảy trang)
   │  VietQR BIN → VietQR short → SePay → [rơi cả 3] chuyển khoản tay
   ▼
Khách quét, chuyển tiền — số tiền & nội dung đã nhúng sẵn trong mã
   ▼
Ngân hàng → SePay → POST webhook về n8n
   │  n8n: regex tách mã đơn khỏi nội dung CK
   │       đối chiếu số tiền → cập nhật trạng thái = da_thanh_toan
   ├─→ Meta CAPI: bắn Purchase (dedup bằng eventID)
   ├─→ Cập nhật bộ đếm chỗ (/webhook/slots)
   └─→ Nhắn Zalo xác nhận + nhắc vào nhóm
```

### 2.2 Mã đơn — thiết kế nhỏ mà quan trọng

```
PRL + [4 số cuối SĐT] + [3 chữ cái ngẫu nhiên]     →  PRL8686XKQ
Nội dung CK:  "PRELA PRL8686XKQ"
```

Bốn tính chất cùng lúc:
- **Người đọc được** — khách đọc qua điện thoại không nhầm.
- **Tự gắn với SĐT** — tự động hỏng thì dò tay vẫn ra người.
- **Có tiền tố thương hiệu** — khách nhìn sao kê biết tiền đi đâu.
- **Không đoán được** — 3 chữ ngẫu nhiên chặn người khác tra đơn người lạ.

Regex đối soát phía n8n: `/PRL\d{4}[A-Z]{3}/`

### 2.3 Lưới an toàn 3 lớp (bài học họ đã trả giá)

Comment trong mã của họ ghi lại đúng sự cố: bản cũ gửi đơn bằng `fetch(..., {mode: 'no-cors'})`. **Kiểu gửi này LUÔN có vẻ thành công kể cả khi server sập** — khách vẫn thấy QR, vẫn chuyển tiền, nhưng đơn không tồn tại; tiền về với một mã lạ, phải dò tay.

Bản hiện tại:

```
Lớp 0  localStorage.setItem(đơn)          ← lưu TRƯỚC khi gửi
Lớp 1  fetch CORS thật, kiểm res.ok
Lớp 2  lỗi → chờ 1,5s → thử lại 1 lần     ← 4G Việt Nam chập chờn
Lớp 3  vẫn lỗi → navigator.sendBeacon()   ← lúc khách rời trang, tab đóng vẫn đi
Lớp 4  bắn event OrderWebhookFailed về Pixel  ← để BIẾT mà sửa
```

**Chép nguyên cả 5 lớp.** Đây là thứ chỉ học được bằng cách mất tiền thật.

### 2.4 QR — 3 nguồn dự phòng nối tiếp

```
1. https://img.vietqr.io/image/{BIN}-{STK}-compact2.png?amount=&addInfo=&accountName=
2. https://img.vietqr.io/image/{TEN_VIET_TAT}-{STK}-compact2.png?...
3. https://qr.sepay.vn/img?acc=&bank=&amount=&des=&template=compact
4. [cả 3 rơi] → hiện bảng chuyển khoản tay + bắn event QrAllSourcesFailed
```

Cài bằng `img.onerror` → nhảy nguồn kế tiếp. Chi tiết dễ sai: **nội dung nhúng trong QR phải trùng từng ký tự với dòng "Nội dung CK" hiển thị trên trang** — lệch nhau là khách quét một đằng, đối soát một nẻo.

### 2.5 Meta CAPI — bắn Purchase phía server

`POST https://graph.facebook.com/v21.0/{pixel_id}/events?access_token=<system_user_token>`

```json
{
  "data": [{
    "event_name": "Purchase",
    "event_time": 1755000000,
    "event_id": "ord_1755000000_ab12cd",
    "action_source": "website",
    "event_source_url": "https://<domain>/",
    "user_data": {
      "ph": "<sha256 của SĐT dạng 84xxxxxxxxx>",
      "fn": "<sha256 của tên, đã lowercase>"
    },
    "custom_data": {
      "value": 399000,
      "currency": "VND",
      "content_name": "Workshop Co May San Xuat Noi Dung"
    }
  }]
}
```

Bốn quy tắc bắt buộc, sai một là báo cáo Meta sai:

1. **`event_id` phải trùng** với `eventID` mà trình duyệt gửi kèm `InitiateCheckout` → chống đếm trùng khi chạy song song Pixel + CAPI.
2. **`ph` chuẩn hoá về `84xxxxxxxxx`** (bỏ dấu `+`, bỏ số 0 đầu) rồi mới SHA256. Không chuẩn hoá là mất hết matching.
3. **`fn` lowercase, bỏ dấu** trước khi hash.
4. **`content_name` phải khớp từng ký tự** với chuỗi bên trình duyệt — chính họ ghi cảnh báo này trong mã: *"Lệch một chữ là Meta tách báo cáo thành hai sản phẩm khác nhau."*

### 2.6 Bộ đếm chỗ — trung thực có kỹ thuật

`GET /webhook/slots` → `{"ok":true,"tong_cho":31,"da_chiem":0,"con_lai":31,"het_cho":false}`

Phía LP: `SLOTS_SHOW_FROM: 15` — **chỉ hiện bộ đếm khi đã bán ≥ 15/31**. Comment của họ: *"bản cũ ghi 'Còn lại 30/30 CHỖ'. Đúng sự thật, nhưng khách đọc ra là 'chưa ai mua'."*

Giấu con số thật lúc bất lợi, **nhưng không bịa con số giả**. Chép đúng ranh giới này.

### 2.7 Danh sách endpoint tối thiểu cần dựng

| Endpoint | Method | Nhiệm vụ |
|---|---|---|
| `/webhook/order-form` | POST | Nhận đơn, ghi DB, giữ chỗ 30 phút |
| `/webhook/slots` | GET | Trả số chỗ còn lại (công khai, cache 30–60s) |
| `/webhook/sepay` | POST | Nhận biến động số dư, đối soát, bắn CAPI, nhắn Zalo |
| `/webhook/expire` (cron) | — | Mỗi 5 phút: đơn quá 30 phút chưa trả → mở lại chỗ |

Bốn cái. Không hơn. Đây là toàn bộ backend của một hệ bán hàng chạy thật.

---

## PHẦN 3 — HỆ 2: Kỹ thuật trang bán hàng

### 3.1 Vì sao 1 file HTML tĩnh là quyết định đúng

185KB, 0 framework, 0 script bên ngoài (Pixel là ngoại lệ duy nhất). Lợi ích thật:

- **Tải nhanh trên 4G Việt Nam** — tệp mục tiêu là người U40–U55 bấm quảng cáo trên điện thoại.
- **Không có build step** → sửa là deploy, deploy là xong. Đó là lý do `last-modified` của họ chỉ cách ngày quét 1 hôm.
- **AI sửa được trực tiếp.** Toàn bộ trang nằm trong một file → dán vào AI, mô tả, nhận file mới. Không có framework nghĩa là không có gì để AI hiểu sai.
- **Backend sập, trang vẫn bán được** (còn QR dự phòng và Zalo).

### 3.2 Ba kỹ thuật tốc độ đáng chép nguyên

```html
<!-- 1. Font không chặn hiển thị -->
<link rel="stylesheet" href="...Be+Vietnam+Pro..." media="print"
      onload="this.media='all';this.onload=null;">
<noscript><link rel="stylesheet" href="..."></noscript>
```
Bản thường khiến trình duyệt **dừng vẽ trang** tới khi tải xong font — trên 4G Việt Nam là 0,3–1 giây màn hình trắng.

```
2. Facade YouTube — hiện ảnh thumbnail i.ytimg.com, bấm mới nhúng iframe
   → tiết kiệm ~1MB mỗi lượt tải (trang có 7 video)

3. preconnect tới fonts.googleapis.com, fonts.gstatic.com, i.ytimg.com
```

### 3.3 Khối `CFG` — điều kiện để LP được bảo trì bằng AI

```js
const CFG = {
  WEBHOOK_URL:  'https://.../webhook/order-form',
  WEBHOOK_CORS: true,
  BANK_BIN: '970422', BANK_SHORT: 'MBBank',
  BANK_ACCOUNT: '...', BANK_HOLDER: '...',
  PRICE_BASE: 399000,
  SLOTS_TOTAL: 31, SLOTS_SHOW_FROM: 15, SLOTS_API: '.../webhook/slots',
  BATCH_DATE: 'Thứ Bảy 23/08 · 14h00–18h00',
  DEADLINE:   '2026-08-22T20:00:00+07:00',
  ZALO_TRAINER: '...', ZALO_GROUP: '...',
  POPUP_DELAY: 45000, POPUP2_DELAY: 60000,
  REAL_SIGNUPS: []        // rỗng = tắt thông báo nổi
};
```

Giá, ngày, số tài khoản, deadline, sức chứa, delay popup — **tất cả ở một chỗ, đầu file**. Người không biết code sửa được. Đây không phải chi tiết nhỏ: nó là **điều kiện cần để một người tự vận hành mà không phụ thuộc lập trình viên**.

### 3.4 Bộ đo lường — chép nguyên

```
PageView → ViewContent
        → HourCalculator{hours_per_day}     ← khách bấm máy tính giờ
        → ScrollDepth{percent}
        → VideoPlay{video}
        → FaqOpen{question}                 ← ⭐ mỏ vàng nghiên cứu
        → CtaClick{cta}
        → PopupShown / Popup2FormShown
        → InitiateCheckout{content_ids:[mã đơn], value, eventID}
        → PaymentClaimed{order_code}        ← khách bấm "đã chuyển khoản"
        → Purchase                          ← server-side, n8n CAPI, dedup
+ báo động: OrderWebhookFailed · QrAllSourcesFailed
```

**`FaqOpen` gửi kèm nguyên văn câu hỏi.** Câu FAQ nào bị mở nhiều nhất chính là nỗi lo lớn nhất của tệp — nghiên cứu thị trường miễn phí, chạy 24/7, tự cập nhật. Đây là event đáng giá nhất trong danh sách và gần như không ai làm.

### 3.5 Hai cơ chế tự bảo vệ

```js
// Hết hạn → khoá form, không nhận tiền cho buổi đã qua
function closeRegistration(){
  note.classList.add('show');
  btn.disabled = true;
  btn.textContent = 'ĐỢT NÀY ĐÃ ĐÓNG — NHẮN ZALO ĐỂ VÀO ĐỢT SAU';
  form.addEventListener('submit', e => e.preventDefault(), true);
  // mọi CTA chuyển hướng sang Zalo
}
```

Và: **giữ chỗ mềm 30 phút** — quá giờ chưa CK thì hệ thống mở lại chỗ. Tạo áp lực thật mà không lừa.

### 3.6 Dấu vết quy trình: 10 ghi chú `KAIZEN:`

Mỗi ghi chú giải thích *bản cũ sai chỗ nào và vì sao sửa*. Ví dụ:
- *"bản cũ chỉ đổi chữ ở đồng hồ, form vẫn nhận tiền cho một buổi đã qua"*
- *"bản cũ dùng thẻ div có onclick → không bấm được bằng bàn phím"*
- *"bản cũ có 2 bộ nghe scroll riêng, một cái không hề dùng"*

Quy trình của họ: **AI dựng → chạy ads → đọc số → AI sửa → ghi lý do vào chính mã nguồn.** Mã nguồn vừa là sản phẩm vừa là nhật ký tối ưu. Đây là lợi thế tốc độ lớn nhất của họ, và là thứ bạn sao chép được ngay hôm nay vì bạn đang có đúng bộ công cụ đó.

---

## PHẦN 4 — HỆ 4 & 6: Vận hành và doanh thu lặp lại

### 4.1 Vì sao không dùng email

Không có ô email trên toàn trang. Comment của họ: *"đã bỏ ô Email. Mọi thứ giao qua Zalo, email chỉ là một ô nữa để khách bỏ dở."*

Chuỗi giao hàng: **QR → nút "Đã chuyển khoản, vào nhóm Zalo" → mọi thứ trong nhóm.** Link nhóm Zalo **chỉ xuất hiện sau khi có mã đơn** — comment ghi rõ: *"KHÔNG đặt link này trong thân trang bán hàng: khách bấm vào là rời trang."*

Nhóm Zalo gánh: link phòng học · checklist 6 điều kiện · nhắc lịch · hỏi đáp · thông báo kèm bù. **Một kênh, không có ai bị bỏ rơi.**

### 4.2 Nhịp vận hành mỗi đợt

```
T-48h   Gửi file kiểm 6 điều kiện vào nhóm Zalo
        (trong đó hướng dẫn bật thanh toán quốc tế — việc DUY NHẤT khách làm trước)
T-0     Buổi 4 tiếng. Chốt: quay màn hình kết quả + xin 1 câu nhận xét NGAY TRONG BUỔI
T+72h   Nhắn Zalo tối đa 3 lần: bản ghi hình · ảnh chuỗi của khách · 1 câu hỏi lấn cấn
        Không trả lời thì dừng
Hàng tuần  Phòng Kèm Bù thứ Bảy 60 phút — chi phí cố định của cam kết,
           đồng thời là nơi bán backend
```

### 4.3 Kinh tế học — nơi tiền thật nằm

```
Front-end:  31 × 399k = 12,4tr/đợt (trần)
            Biến phí/học viên ≈ 0đ (khách tự trả API bằng khóa riêng)
            Định phí/đợt = 4h dạy + 1h/tuần kèm bù

Back-end:   PRELA Cloud 686k/tháng  ← doanh thu LẶP LẠI
            Lộ trình 5 buổi còn lại, 399k được trừ hết
```

**Đây không phải mô hình bán workshop. Đây là mô hình thuê bao, dùng workshop 399k làm cửa vào.** Front-end chỉ để: hoàn vốn quảng cáo · lọc khách · sản xuất bằng chứng · tạo nợ ân tình trước lúc pitch.

Và gói vận hành hộ có lý do kỹ thuật thật, không phải bịa: Facebook đổi API, token hỏng, Google Sheets đổi quota, n8n cần cập nhật. **Rủi ro bên thứ ba chính là sản phẩm của gói 686k.**

---

## PHẦN 5 — Bản của bạn: Coachio Mây

### 5.1 So sánh hai hệ

| | Cỗ Máy (họ) | Mây (bạn) |
|---|---|---|
| Lõi | n8n workflow | OpenClaw engine |
| Bộ nhớ | Google Sheets | `SOUL.md` · `USER.md` · `IDENTITY.md` |
| Luật làm việc | Prompt trong node | `AGENTS.md` |
| Kỹ năng | 1 (đăng bài) | Nhiều: `viral-writer` · `tu-van` · `jina` · `social-extract` · `coachio-image` |
| Kênh | Facebook Page API | **Telegram Bot API** |
| Model | Claude (khóa khách) | DeepSeek (khóa khách) |
| Nơi chạy | Cloud của họ / máy khách | **Railway 24/7** (đã có Dockerfile + start.sh) |
| Rủi ro nền tảng | **Cao** (Meta đổi API, token, chính sách nội dung) | **Thấp** (Telegram bot token không hết hạn) |
| Rào cản vào | **Thẻ Visa quốc tế** ← chốt chặn lớn nhất | Nhẹ hơn |
| Khoảnh khắc bán hàng | Bài lên page | **Mây trả lời tin nhắn đầu tiên, gọi đúng tên** |

**Ba lợi thế cấu trúc bạn có:**

1. **Ít gãy hơn.** Telegram bot token không hết hạn; không có App Review; không có chính sách nội dung kiểu Meta. Cái làm nên gói 686k của họ (rủi ro Facebook) thì bạn không có — nhưng bạn có thứ khác để bán: **giữ Mây sống 24/7 trên hạ tầng, cập nhật engine, thêm kỹ năng.**
2. **Sản phẩm nói chuyện lại.** Khoảnh khắc *"Mây trả lời và gọi đúng tên tôi"* mạnh hơn hẳn *"một bài đăng lên page"* — nó có tính người, và nó xảy ra trong 5 giây thay vì sau một chuỗi 7 node.
3. **Không gian nâng cấp rộng.** Họ phải viết trên trang: *"chuỗi này đăng bài, nó không bán hàng thay bạn."* Bạn không bị giới hạn đó — mỗi skill mới là một món bán thêm.

**Một điểm yếu phải xử lý thẳng:** quy trình cài của bạn **nhiều bước hơn** của họ (Node/pnpm hoặc Railway + GitHub + BotFather + Getmyid + DeepSeek key + biến môi trường + `OPENCLAW_HOME`). Họ chỉ có: nhập 1 file chuỗi + nối page + dán khóa. Vũ khí của bạn là **"câu thần chú"** trong `BAT-DAU.md` — nhưng phải đo thật: **người không biết code mất bao lâu?** Nếu quá 90 phút, buổi 4 tiếng sẽ vỡ. Đo trước khi mở bán.

### 5.2 Lịch trình 4 tiếng — bản Mây

```
0:00–0:15  Điểm danh, kiểm 5 điều kiện
0:15–0:40  Lấy 3 chìa khoá CÙNG NHAU, chia màn hình, bấm từng nút:
           DeepSeek key · BotFather token · Telegram ID
           ← đây là "chỗ 8/10 người bỏ cuộc" phiên bản của bạn
0:40–1:00  ⭐ CHIẾN THẮNG ĐẦU: bot hiện tên trong Telegram (chưa cần chạy)
           ← BẮT BUỘC rơi trước phút 60
1:00–1:45  Deploy Railway bằng câu thần chú — AI làm, khách kiểm chứng
1:45–2:00  Nghỉ
2:00–3:00  🔥 KHOẢNH KHẮC: nhắn → Mây trả lời → đặt tên → cá tính hoá
           → CHỤP MÀN HÌNH NGAY
3:00–3:25  Gắn kỹ năng + 5 lỗi hay gặp (409 Conflict · sai OPENCLAW_HOME ·
           thiếu auth store DeepSeek · Volume chưa gắn · pair sai ID)
3:25–3:40  15 phút giới thiệu lộ trình — CÓ ĐỒNG HỒ, ghi rõ trên trang
3:40–4:00  Hỏi đáp mở + ghi tên vào phòng kèm bù
```

Nguyên tắc bất di bất dịch: **chiến thắng nhỏ phải rơi trước phút 60.** Họ đặt ở 0:35–0:55. Người mất niềm tin trong giờ đầu sẽ không quay lại ở giờ thứ ba.

### 5.3 Sáu bộ phận "dưới nắp capo" của Mây

Khối 09 phiên bản bạn — nội dung đã có sẵn trong `README.md`, chỉ cần viết lại cho người không biết code đọc:

| # | Bộ phận | Nói với khách thế nào |
|---|---|---|
| 1 | **Engine OpenClaw** | Cái máy. Bạn không cần hiểu nó, nhưng nó là mã nguồn mở — không ai tắt được của bạn. |
| 2 | **`SOUL.md` + `USER.md`** | Tính cách và trí nhớ của Mây. Sửa file này là Mây đổi tính. Nó nhớ bạn là ai. |
| 3 | **`AGENTS.md`** | Luật làm việc: fact-check, không từ chối ẩu, bảo mật. Đây là lý do Mây không nói bừa. |
| 4 | **Thư mục `skills/`** | Mỗi thư mục là một nghề Mây biết làm. Thêm thư mục = thêm nghề. |
| 5 | **Khóa DeepSeek mang tên bạn** | Tài khoản bạn, tiền bạn, không qua tay ai. Mây sống kể cả khi bạn không còn liên quan gì đến tôi. |
| 6 | **Railway + Volume `/data`** | Nơi Mây ở, chạy 24/7. Bạn tắt máy tính, Mây vẫn thức. |

### 5.4 Bảng ưu tiên thi công

| Ưu tiên | Việc | Ghi chú |
|---|---|---|
| **P0** | LP 1 file + khối `CFG` đầu file | Giá/ngày/STK/deadline/sức chứa ở một chỗ |
| **P0** | Form 2 ô (Tên + SĐT) → QR VietQR → nhóm Zalo/Telegram | Bỏ email. Mã đơn: 3 chữ + 4 số cuối SĐT + 3 chữ ngẫu nhiên |
| **P0** | Meta Pixel + đủ bộ event (mục 3.4) | Không đo thì không tối ưu được. Ngày 1. |
| **P0** | Quay video demo: nhắn → Mây trả lời → đặt tên (2 phút, màn hình thật) | Tài sản bán hàng số 1 |
| **P1** | Webhook nhận đơn — n8n self-host **hoặc** Cloudflare Worker / Google Apps Script | Bật CORS thật. **Tuyệt đối không dùng `no-cors`.** |
| **P1** | SePay webhook → đối soát theo nội dung CK | Rẻ, chạy tốt ở VN |
| **P1** | Lưới an toàn 5 lớp cho đơn hàng (mục 2.3) | Bài học họ trả giá, bạn lấy miễn phí |
| **P1** | Đo thời gian cài đặt thật với 3 người không biết code | Quyết định lịch trình 4 tiếng có khả thi không |
| **P2** | API đếm chỗ + quy tắc chỉ hiện khi bán ≥ nửa | Trung thực mà vẫn tạo áp lực |
| **P2** | CAPI server-side Purchase, dedup bằng eventID | Cần khi bắt đầu scale ads |
| **P2** | Nhật ký hội thoại + chi phí token cho khách xem | Nâng cấp so với họ |
| **P3** | ref/UTM cookie 60 ngày | Hạ tầng affiliate |
| **P3** | Đường thoát trần 31 người | Trợ giảng 1:8, hoặc bản "tự lắp có AI kèm" giá thấp hơn |

### 5.5 Lịch 4 tuần

```
Tuần 1  Dựng LP + webhook + QR + Pixel. Quay video demo Mây.
        Chốt: ngày đợt 1 · sức chứa 20–31 · 5 điều kiện tham gia.
        ĐO: người không biết code cài Mây mất bao lâu?
Tuần 2  Ads nhỏ 200–500k/ngày. Đọc HourCalculator · ScrollDepth · FaqOpen.
        Câu FAQ nào mở nhiều nhất → viết lại khối tương ứng.
Tuần 3  Dạy đợt 1. BẮT BUỘC: quay màn hình kết quả + xin nhận xét NGAY TRONG BUỔI.
Tuần 4  Nhét bằng chứng đợt 1 vào trang. Mở đợt 2. Tăng giá đúng như đã cam kết.
Hàng tuần  Phòng kèm bù 60 phút, giờ cố định. Đây là nơi bán gói vận hành hộ.
```

---

## PHẦN 6 — Rủi ro và ranh giới

| Rủi ro | Xử lý |
|---|---|
| **Chép câu chữ của họ** | Đừng. Cấu trúc tự do, câu chữ là tài sản của họ — và tệp coach VN nhỏ, trùng câu là bị nhận ra trong một ngày. |
| **Chép số thống kê của họ** | "8/10 người bỏ cuộc", "51+ chuỗi", "360 triệu" là số của họ. Dùng số của bạn, kể cả khi nhỏ hơn. *"Đây là đợt đầu tiên"* là câu bán hàng hợp lệ và mạnh. |
| **Claim thu nhập** | Meta Ads siết rất chặt. Chú ý: *"15 phút có 7 người nhắn tin"* trên trang họ là **tin nhắn học viên**, không phải cam kết của họ — giữ đúng ranh giới đó khi viết. |
| **Cam kết hoàn tiền khi chưa tính chi phí** | Cam kết của họ rẻ vì kết quả nghiệm thu được trong buổi + điều kiện "phải vào kèm bù ít nhất một lần". Nếu sản phẩm bạn không nghiệm thu được trong buổi, đừng chép cam kết này. |
| **Mở bán khi chưa có backend** | 399k × 31 không nuôi nổi ads nếu không có doanh thu lặp lại. Chốt giá gói vận hành hộ **trước** đợt 1. |
| **Social proof giả** | Họ có sẵn cơ chế mà chủ động không dùng. Có lý do. |
| **Trần 31 người** | Đây cũng sẽ là trần của bạn. Thiết kế đường thoát trước khi bị chặn. |
| **Khoá API của khách** | Tuyệt đối không giữ hộ, không markup. Đây là lời hứa bán hàng mạnh nhất — và cũng là thứ khiến bạn ngủ ngon khi có sự cố. |

---

## Checklist thi công

**Hệ sản phẩm (Mây)**
- [ ] Đo thời gian cài thật với 3 người không biết code → quyết lịch trình
- [ ] Rút gọn còn 1 "câu thần chú" + 3 chìa khoá
- [ ] Nhật ký hội thoại + chi phí token, khách mở xem được
- [ ] Hàng rào chất lượng + báo lỗi về Telegram chủ máy
- [ ] Danh sách 5 lỗi hay gặp + cách tự sửa (tài liệu phát trong buổi)

**Hệ bán hàng**
- [ ] LP 1 file, 26 khối, khối `CFG` đầu file
- [ ] Form 2 ô → mã đơn → QR 3 nguồn → nhóm Zalo
- [ ] Meta Pixel + đủ bộ custom event (đặc biệt `FaqOpen` kèm nội dung câu hỏi)
- [ ] 4 endpoint: `order-form` · `slots` · `sepay` · `expire`
- [ ] Lưới an toàn 5 lớp + 2 event báo động
- [ ] CAPI Purchase dedup bằng eventID, `content_name` khớp từng ký tự
- [ ] Deadline tự khoá form + giữ chỗ mềm 30 phút

**Hệ vận hành**
- [ ] Checklist 5 điều kiện, gửi trước buổi 48h
- [ ] Giờ cố định phòng kèm bù hàng tuần
- [ ] Quy trình xin bằng chứng NGAY TRONG BUỔI (không xin sau)
- [ ] Chốt giá gói vận hành hộ trước khi mở bán đợt 1

---

*Tài liệu kỹ thuật nội bộ. Dữ liệu quét ngày 12/08/2026 từ nguồn công khai.*
