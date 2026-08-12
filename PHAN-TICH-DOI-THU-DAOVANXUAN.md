# Bóc tách hệ thống bán hàng daovanxuan.com — và bản đồ dựng hệ tương tự cho Coachio Mây

> Nguồn: `https://daovanxuan.com/` — tải ngày 12/08/2026. Trang single-file 185KB, 26 khối,
> đã đọc toàn bộ HTML/CSS/JS, khối cấu hình ẩn `CFG`, và gọi thử API công khai của họ.
> Tài liệu này phân tích **cấu trúc và cơ chế**, không sao chép câu chữ. Copy nguyên văn = vừa
> rủi ro pháp lý vừa mất khác biệt. Cái đáng lấy là **bộ khung**, không phải câu chữ.

---

## PHẦN 0 — Tóm tắt một trang

| Hạng mục | Của họ |
|---|---|
| Sản phẩm mồi | Workshop live 4 tiếng "Cỗ Máy Sản Xuất Nội Dung" |
| Giá | **399.000đ** (đợt sáng lập) · giá "thật" 1.686.000đ từ đợt 4 |
| Value stack niêm yết | 5.702.000đ (7 món) → chiết khấu biểu kiến 93% |
| Sức chứa | 31 người/đợt (có lý do cơ học, không phải khan hiếm giả) |
| Doanh thu/đợt tối đa | ~12,4tr (front-end gần như chỉ để hoàn vốn quảng cáo) |
| Backend thật | ① PRELA Cloud **686k/tháng** (vận hành hộ) ② Lộ trình 5 buổi còn lại, 399k được trừ hết |
| Kênh traffic | Facebook Ads (utm_source=fb, có campaign/adset/ad id, Pixel + domain verification) |
| Kênh giao hàng | **Zalo group** — không dùng email |
| Thanh toán | QR VietQR/SePay, đối soát tự động qua nội dung CK |
| Hạ tầng | HTML tĩnh 1 file + **n8n self-host** (`n8n2.daovanxuan.com`) + SePay webhook |
| Trạng thái hiện tại | API `/webhook/slots` trả `{tong_cho:31, da_chiem:0, con_lai:31}` → đợt 23/08 **chưa bán được suất nào** tại thời điểm quét |

**Công thức lõi của họ, gói trong một câu:**
> Bán **một vật thể chạy được, lắp xong trong khung giờ bán hàng**, chứ không bán kiến thức —
> để mọi phản đối của khách quy về đúng một câu duy nhất, rồi thiết kế toàn bộ trang để giết đúng câu đó.

Câu phản đối duy nhất đó là: *"Tôi mua khóa học rồi bỏ xó."*
Đọc lại 26 khối, bạn sẽ thấy **không có khối nào không phục vụ việc giết câu đó.**

---

## PHẦN 1 — Kiến trúc chào hàng (Offer Architecture)

### 1.1 Cơ chế đặt tên riêng — "Cỗ Máy Sản Xuất Nội Dung™"

Không bán "khóa học AI". Bán một **cơ chế có tên riêng, có ký hiệu ™**, được mô tả như
"nhân viên số đầu tiên trong đội AI của bạn". Ba tác dụng:

1. **Thoát so sánh giá.** Không ai so 399k với "khóa AI 3–8 triệu" nữa vì đây là *loại khác*.
2. **Biến phần mềm thành người.** "Không xin nghỉ phép, không đòi tăng lương" → so kè trực tiếp
   với chi phí thuê 1 bạn content 6tr/tháng. Đây là **neo giá (anchor) bằng nhân sự**, không phải bằng khóa học.
3. **Có thể tháo ra xem.** Khối 09 "Dưới nắp capo" liệt kê 6 bộ phận. Minh bạch kỹ thuật
   → khách tin là có thật, không phải hứa.

### 1.2 Chuyển "kết quả" vào bên trong buổi bán hàng

Đây là **đòn mạnh nhất của họ và là thứ khó bắt chước nhất**:

- Kết quả bán được **nghiệm thu ngay trong 4 tiếng**: bài thật lên page thật + **ảnh chụp màn hình**.
- Vì kết quả nghiệm thu được ngay → cam kết hoàn tiền rẻ đi rất nhiều.
- Vì kết quả nghiệm thu được ngay → bằng chứng cho đợt sau **tự sinh ra** từ chính khách đợt này
  (họ nói thẳng: 399k đổi lấy quyền quay màn hình + 1 câu nhận xét).

Đây là vòng lặp tự nuôi: **bán rẻ → thu bằng chứng → tăng giá → bán tiếp bằng bằng chứng đó.**

### 1.3 Value stack và trò chơi con số

| Món | Giá niêm yết |
|---|---|
| Buổi lắp ráp 4 tiếng (31 người, có kèm) | 1.686.000đ |
| Kèm #1 — File chuỗi dựng sẵn | 986.000đ |
| Kèm #2 — Lấy khóa Claude ngay trong buổi | 486.000đ |
| Kèm #3 — 365 prompt đăng bài | 686.000đ |
| Kèm #4 — 100 mẫu hook | 386.000đ |
| Kèm #5 — Phòng kèm bù thứ Bảy (vô hạn) | 986.000đ |
| Kèm #6 — Bản ghi hình trọn đời | 486.000đ |
| **Tổng** | **5.702.000đ** |

Ba chi tiết dễ bỏ sót:

1. **Tất cả đều kết thúc bằng "86"** — 1.686 / 986 / 486 / 686 / 386. Zalo của họ là 0946728**686**,
   PRELA Cloud **686**k/tháng, chi phí API "8.600đ/tháng". Đây là **branding bằng con số** (86 = "phát").
   Nó tạo cảm giác cùng một hệ, do một người định giá — không phải bịa ngẫu nhiên.
2. **399.000đ là con số DUY NHẤT không theo hệ 86.** Cố ý: giá vào cửa nằm ngoài hệ giá thật,
   nên nó "không thuộc bảng giá" → dễ chấp nhận là ngoại lệ.
3. **Neo hai tầng:** 5.702.000 (tổng trị giá) → 1.686.000 (giá bán lẻ thật từ đợt 4) → 399.000 (đợt sáng lập).
   Neo hai tầng đáng tin hơn neo một tầng, vì tầng giữa là con số họ **cam kết sẽ quay về**.

### 1.4 Lý do giảm giá (reason-why) — trung thực và có ràng buộc

> "Vì tôi đang cần bằng chứng. Đây là 3 đợt sáng lập đầu tiên... Đổi lại 399K, tôi xin phép
> quay màn hình kết quả của bạn và xin một câu nhận xét. Bạn không muốn quay cũng không sao."

Bốn tầng tác dụng: giải thích giá rẻ (không rẻ vì kém) → tạo có đi có lại → **tự ràng buộc công khai**
("Từ đợt thứ 4 về đúng giá 1.686.000đ. Tôi ghi ra đây thì tôi làm thật") → và **cho phép từ chối**
(lời mời có đường thoát thì đáng tin gấp đôi).

### 1.5 Cam kết 3 lớp — trả bằng công trước, bằng tiền sau

| Lớp | Nội dung | Chi phí thật cho họ |
|---|---|---|
| 1 | Chưa xong → vào Phòng Kèm Bù thứ Bảy, vô hạn buổi | **1 giờ/tuần cố định**, bất kể 5 hay 50 người |
| 2 | Qua kèm bù vẫn không chạy → hoàn 100% trong 48h, giữ nguyên tài liệu | Hiếm khi kích hoạt |
| 3 | 7 ngày, nhắn Zalo 1 câu, không tra hỏi, không giữ chân | Thấp |

Và họ **nói thẳng ra kinh tế học của cam kết** ngay trên trang:
> "Vì sao tôi dám? Vì cam kết này tốn của tôi 1 giờ mỗi tuần cố định... Còn hoàn tiền thì tôi mất
> cả tiền lẫn 4 giờ đã bỏ ra. Nên tôi có mọi động cơ để ngồi cùng bạn đến khi xong."

Đây là **giải thích động cơ** — cấp độ cao hơn "cam kết hoàn tiền" thông thường. Khách không tin
lời hứa, khách tin **cấu trúc lợi ích**.

**Cửa hậu kỹ thuật:** điều kiện hoàn tiền = phải đủ 6 điều kiện tham gia **và đã vào Phòng Kèm Bù
ít nhất một lần**. Nghĩa là mọi yêu cầu hoàn tiền đều đi qua ít nhất một buổi ngồi cùng họ.
Tỷ lệ hoàn thực tế gần như bằng 0. Cam kết nghe rất to, chi phí rất nhỏ — **đây là kỹ thuật, không phải lừa**.

### 1.6 Sàng lọc ngược — "ĐỪNG mua nếu..." đặt TRƯỚC "Mua nếu..."

Sáu dòng loại trừ trước, sáu dòng chấp nhận sau. Trong đó có một dòng là **đòn tâm lý chính xác vào tệp**:

> "Trên 40 tuổi, không rành công nghệ, và hơi ngại thừa nhận điều đó"

Câu này gọi tên **nỗi xấu hổ giấu kín** của đúng tệp mục tiêu (coach/trainer/chuyên gia U40–U55).
Người đọc thấy mình bị đọc vị → tin rằng người viết hiểu mình → tin luôn phần còn lại.
Đây là kỹ thuật NLP (họ là NLP Trainer — điều đó thể hiện rõ trong toàn bộ câu chữ).

### 1.7 Minh bạch phần bán hàng — "3:25 → 3:40 · Tôi nói về 5 buổi còn lại, đúng 15 phút, có đồng hồ"

Ghi thẳng phần pitch vào lịch trình, và có hẳn câu FAQ #8 *"Đây có phải khóa học bán khóa học không?"*
trả lời **"Có"**. Nghịch lý: thú nhận ý đồ bán hàng làm tăng tin cậy cho toàn trang.
Đây là **tiêm phòng phản đối** (objection inoculation) — nêu phản đối trước khi khách nêu.

### 1.8 Diệt nỗi sợ phụ thuộc — "Khóa Claude mang tên bạn"

> "Tôi không đứng giữa, không lấy phần trăm, và chuỗi của bạn vẫn chạy kể cả khi bạn không còn
> liên quan gì đến tôi."

Chủ động **từ bỏ** mô hình khóa dùng chung / bán API markup — thứ dễ ăn tiền nhất — để lấy niềm tin.
Rồi bán lại sự phụ thuộc ở dạng **tùy chọn, có giá minh bạch**: PRELA Cloud 686k/tháng.
Khách được quyền tự chủ → nên khách sẵn sàng trả tiền để không phải tự chủ. Rất tinh.

Và họ công bố **chi phí vận hành thật**: 290đ/bài, ~8.600đ/tháng, nạp 130k dùng hơn một năm.
Con số nhỏ đến mức tự nó thành lý lẽ bán hàng.

---

## PHẦN 2 — Công thức viết trang (26 khối)

Thứ tự này lấy từ chính comment trong mã nguồn của họ (`<!-- KHỐI 01 … KHỐI 26 -->`).
Đây là **bộ khung tái sử dụng được** — thứ đáng giá nhất trong toàn bộ tài liệu này.

| # | Khối | Nhiệm vụ tâm lý |
|---|---|---|
| 01 | Thanh dính — **không nêu giá** | Giữ CTA luôn trong tầm tay, chưa lộ giá |
| 02 | Hero: "Tôi ngồi cùng bạn 4 tiếng — cho đến khi nó chạy" | Lời hứa + người chịu trách nhiệm, trong 1 câu |
| 03 | Video "xem cái chuỗi đó chạy trước đã" | Bằng chứng vận hành trước mọi lời nói |
| 04 | **Máy tính giờ tương tác** | Khách **tự tính ra nỗi đau bằng con số của chính mình** |
| 05 | "Sáng mai, nếu bạn mở Fanpage ra" | Trạng thái tương lai, hiện tại hoá bằng cảm giác |
| 06 | "Không phải bạn lười. Là bạn kẹt ở đúng ba chỗ." | Gỡ tội cho khách + chẩn đoán 3 chỗ kẹt |
| 07 | "6 năm. Hơn 360 triệu. Hai lần sập." | Câu chuyện **thất bại**, không phải thành công |
| 08 | Cơ chế 4 bước có tên ™ | Biến sản phẩm thành thực thể có logic |
| 09 | "Dưới nắp capo" — 6 bộ phận | Minh bạch kỹ thuật cho người hoài nghi |
| 10 | Cách cũ vs cách mới (2 cột) | Định vị đối lập với "khóa học" |
| 11 | 6 thứ mang về | Kết quả **cầm nắm được**, không phải "kiến thức" |
| 12 | Lịch trình từng 15–20 phút | Diệt sợ mơ hồ + nhét phần pitch vào công khai |
| 13 | Video học viên | Bằng chứng bên thứ ba |
| 14 | Ảnh tin nhắn học viên | Bằng chứng thô, khó dàn dựng |
| 15 | Về trainer (đặt SAU bằng chứng) | Uy tín đến sau kết quả, không đến trước |
| 16 | Sàng lọc: **ĐỪNG mua** trước, **Mua** sau | Đảo chiều áp lực → tăng khao khát |
| 17 | 6 điều kiện tham gia | Gán trách nhiệm cho khách, bảo vệ cam kết |
| 18 | Cam kết 3 lớp + giải thích động cơ | Đảo rủi ro |
| 19 | Value stack 5.702.000đ | Neo giá |
| 20 | **Bảng giá — lần đầu lộ giá (khối 20/26 ≈ 77% chiều sâu)** | Giá chỉ xuất hiện khi giá trị đã đầy |
| 21 | 399k đứng cạnh cái gì (3 cột + "nếu không làm gì") | Đổi hệ quy chiếu chi phí |
| 22 | Khan hiếm 31 suất + đếm ngược | Ép hành động, có lý do cơ học |
| 23 | FAQ 12 câu | Dọn phản đối cuối |
| 24 | Form 2 ô → QR ngay tại chỗ | Ma sát tối thiểu |
| 25 | Lời nhắn cuối P.S. / P.P.S. | Nhắc lại câu chuyện + mở đường hỏi riêng |
| 26 | (đã gộp vào 24) | — |

**Bốn nguyên tắc rút ra từ thứ tự này:**

1. **Giá xuất hiện ở 77% chiều sâu trang** — sau cam kết, sau value stack, trước khan hiếm.
   Thanh dính cố ý **không nêu giá** (comment trong mã ghi rõ "KHÔNG NÊU GIÁ").
2. **Bằng chứng (13–14) đặt TRƯỚC tiểu sử trainer (15).** Kết quả nói trước, danh hiệu nói sau.
3. **Khối 04 là khối quan trọng nhất và ít người làm.** Không "kể" nỗi đau — bắt khách bấm 1 nút
   rồi **tự nhìn thấy con số giờ và tiền của chính mình**. Con số do khách tự tạo thì khách không cãi.
   Con số đó còn được dùng lại ở khối 21 ("Nếu bạn không làm gì cả") và gửi kèm vào đơn hàng (`hoursPerDay`).
4. **Câu chuyện là chuyện THẤT BẠI, không phải chuyện thành công.** 360 triệu, hai lần sập,
   và cú twist: *"thứ đầu tiên đáng lẽ tôi phải làm, tôi lại làm sau cùng. Nó mất của tôi 4 tiếng."*
   Đây chính là **lý do tồn tại của sản phẩm**, kể dưới dạng tiếc nuối cá nhân.

### Giọng văn — 5 quy tắc họ tuân thủ tuyệt đối

1. **Không dùng từ đại ngôn.** Họ viết thẳng: *"Không phải 'làm chủ AI'. Không phải 'chuyển đổi số'. Chỉ là một cái chuỗi. Chạy được."*
2. **Câu cực ngắn xen câu dài.** Nhịp đọc trên điện thoại.
3. **Nêu điểm yếu trước khi khách phát hiện.** *"Thật lòng: tuần đầu bạn sẽ phải sửa."*
4. **Từ chối hứa cái không hứa được.** FAQ #6 về rủi ro Facebook: *"Tôi không hứa 'chắc chắn không' — ai hứa thì bạn nên cảnh giác."* Từ chối hứa = tăng tin cậy cho những lời hứa còn lại.
5. **Ngôi thứ nhất, một người, có số điện thoại thật.** Không "chúng tôi", không "đội ngũ".

---

## PHẦN 3 — Hạ tầng kỹ thuật (bóc từ mã nguồn)

### 3.1 Sơ đồ hệ thống

```
Facebook Ads (utm_source=fb, campaign/adset/ad id)
        │
        ▼
Landing page tĩnh 1 file HTML (185KB, 0 thư viện ngoài)
   ├── Meta Pixel 1089016496553404 + Advanced Matching (tên/SĐT)
   ├── ref/UTM → cookie 60 ngày (hạ tầng cho affiliate)
   ├── GET  n8n2.daovanxuan.com/webhook/slots       → đếm chỗ còn lại (thật)
   └── POST n8n2.daovanxuan.com/webhook/order-form  → tạo đơn
        │
        ▼
n8n self-host  ──► sinh/ghi đơn, giữ chỗ 30 phút
        │
        ▼
QR VietQR (BIN) → VietQR (short) → SePay  [3 nguồn dự phòng] → chuyển khoản tay
        │
        ▼
Khách chuyển khoản, nội dung "PRELA PRL####XYZ"
        │
        ▼
SePay webhook → n8n đối soát theo nội dung CK → xác nhận đơn
        │
        ├──► Meta CAPI: Purchase (dedup bằng eventID khớp với InitiateCheckout)
        └──► Zalo group học viên (link chỉ hiện SAU khi có mã đơn)
```

### 3.2 Những quyết định kỹ thuật đáng chép

| Quyết định | Vì sao đáng chép |
|---|---|
| **1 file HTML, 0 framework, 0 script ngoài** | Tải cực nhanh trên 4G Việt Nam. Font Google load kiểu `media="print"→onload` để không chặn hiển thị. Video YouTube dùng ảnh thumbnail `i.ytimg.com`, bấm mới nhúng iframe (facade) → tiết kiệm ~1MB/lượt tải. |
| **Khối `CFG` ở đầu file JS** | Giá, số tài khoản, ngày đợt, deadline, sức chứa, delay popup — tất cả ở một chỗ, người không biết code sửa được. **Đây là điều kiện để LP được bảo trì bằng AI.** |
| **Form chỉ 2 ô: Tên + SĐT** | Comment trong mã: *"đã bỏ ô Email. Mọi thứ giao qua Zalo"*. Tệp Việt Nam ít check mail. Mỗi ô bỏ đi = tăng tỷ lệ điền. |
| **Mã đơn `PRL` + 4 số cuối SĐT + 3 chữ ngẫu nhiên** | Người đọc được, tự gắn với SĐT → đối soát tay vẫn ra khi tự động hỏng. |
| **Nội dung CK có tiền tố `PRELA`** | Khách nhìn sao kê biết tiền đi đâu; n8n vẫn tách được mã đơn. |
| **QR 3 nguồn dự phòng + fallback CK tay** | Nguồn QR chết không làm mất đơn. Có cả event `QrAllSourcesFailed` để biết mà sửa. |
| **Lưới an toàn cho đơn hàng** | Lưu `localStorage` trước khi gửi → retry 2 lần → `sendBeacon` lúc rời trang → bắn `OrderWebhookFailed` về Pixel để báo động. Họ từng mất đơn vì dùng `no-cors` (mode này *luôn* báo thành công kể cả khi server sập) — comment trong mã ghi lại đúng bài học đó. |
| **Deadline tự khoá form** (`closeRegistration()`) | Hết hạn: nút đổi chữ, form chặn submit, mọi CTA chuyển hướng sang Zalo. Không nhận tiền cho buổi đã qua. |
| **Giữ chỗ mềm 30 phút** | Tạo áp lực thật mà không lừa: quá giờ chưa CK thì mở lại chỗ. |

### 3.3 Hai chi tiết về sự trung thực — nên chép nguyên tinh thần

1. **`SLOTS_SHOW_FROM: 15`** — bộ đếm chỗ chỉ hiện ra khi **đã bán được ≥15 chỗ**.
   Comment của họ: *"bản cũ ghi 'Còn lại 30/30 CHỖ'. Đúng sự thật, nhưng khách đọc ra là 'chưa ai mua'."*
   → Giấu con số thật lúc bất lợi, **nhưng không bịa con số giả**. Ranh giới rất đẹp.
2. **`REAL_SIGNUPS: []`** — thông báo nổi kiểu "anh A vừa đặt chỗ" **đang TẮT**, với ghi chú:
   *"⚠️ ĐỂ MẢNG RỖNG = TẮT. Chỉ điền TÊN THẬT của người đã đặt chỗ thật."*
   → Họ có sẵn cơ chế social proof giả nhưng **chủ động không dùng**.

Hai chi tiết này là lý do trang của họ "đọc thấy tin được". Nếu chép cấu trúc mà bỏ tinh thần này,
bạn sẽ ra một trang giống hệt nhưng **có mùi**, và tệp U40 ngửi ra rất nhanh.

### 3.4 Bộ đo lường (đáng chép nguyên xi)

Sự kiện Pixel họ bắn, theo đúng hành trình:

```
PageView → ViewContent → HourCalculator{hours_per_day}
        → ScrollDepth{percent} → VideoPlay{video} → FaqOpen{question}
        → CtaClick{cta} → PopupShown / Popup2FormShown
        → InitiateCheckout{content_ids:[mã đơn], value, eventID}
        → PaymentClaimed{order_code}            (khách bấm "đã chuyển khoản")
        → Purchase                              (server-side qua n8n CAPI, dedup bằng eventID)
        + báo động: OrderWebhookFailed / QrAllSourcesFailed
```

Ba điểm tinh:
- **`FaqOpen` gửi kèm nội dung câu hỏi** — câu FAQ nào mở nhiều nhất chính là **nỗi lo lớn nhất của tệp**.
  Đây là công cụ nghiên cứu thị trường miễn phí, chạy liên tục.
- **`content_name` phải khớp từng ký tự** giữa Pixel phía trình duyệt và CAPI phía n8n,
  nếu không Meta tách thành 2 sản phẩm khác nhau và báo cáo sai.
- **`eventID` khớp giữa InitiateCheckout và Purchase** → chống đếm trùng khi dùng cả Pixel lẫn CAPI.

### 3.5 Dấu vết cho thấy trang này do AI dựng và bảo trì

10 ghi chú `KAIZEN:` trong mã, mỗi ghi chú giải thích **bản cũ sai chỗ nào và vì sao sửa**.
Ví dụ: *"bản cũ chỉ đổi chữ ở đồng hồ, form vẫn nhận tiền cho một buổi đã qua"*.

Nghĩa là quy trình của họ là: **AI dựng → chạy ads → đọc số → AI sửa → ghi lại lý do vào chính mã nguồn.**
Mã nguồn vừa là sản phẩm vừa là nhật ký tối ưu. Đây là lợi thế tốc độ lớn nhất của họ — và là thứ
**bạn có thể sao chép ngay hôm nay**, vì bạn đang có đúng bộ công cụ đó.

---

## PHẦN 4 — Kinh tế học của mô hình

```
Đợt sáng lập:  31 suất × 399.000đ  =  12.369.000đ   (trần)
Chi phí biến đổi/học viên          ≈  0đ            (khách tự trả API bằng khóa riêng)
Chi phí cố định/đợt                =  4h dạy + 1h/tuần kèm bù
```

Front-end **không phải chỗ kiếm tiền**. Nó là:
1. **Máy hoàn vốn quảng cáo** (self-liquidating offer): 399k đủ trả CPA cho tệp coach VN.
2. **Máy lọc khách**: người chịu ngồi 4 tiếng làm việc thật = người sẽ mua tiếp.
3. **Máy sản xuất bằng chứng**: mỗi đợt sinh ra video màn hình + nhận xét cho đợt sau.
4. **Máy tạo khoảnh khắc nợ ân tình**: ngồi cùng đến khi chạy → có đi có lại rất mạnh trước lúc pitch.

Tiền thật nằm ở:
- **PRELA Cloud 686k/tháng** — doanh thu lặp lại. 31 người × 20% chuyển đổi ≈ 4,2tr/tháng/đợt, cộng dồn.
- **Lộ trình 5 buổi còn lại** — 399k được trừ hết nếu học tiếp (tripwire hoàn tín dụng toàn phần).

**Kết luận chiến lược:** đây không phải mô hình bán workshop. Đây là **mô hình thuê bao,
dùng workshop 399k làm cửa vào**. Nếu bạn chép mà thiếu backend thuê bao, bạn sẽ dạy 4 tiếng
lấy 399k và lỗ công.

---

## PHẦN 5 — Điểm yếu của họ (chỗ bạn chen vào được)

| Điểm yếu | Cơ hội cho Coachio Mây |
|---|---|
| **Phụ thuộc Facebook API.** Cổng nối Fanpage là "bước hay lỗi nhất" (chính họ thừa nhận). Facebook đổi chính sách/token hết hạn → chuỗi chết hàng loạt, họ phải sửa cho 31×N người. | Mây chạy trên **Telegram** — API ổn định, token không hết hạn, không có chính sách nội dung kiểu Meta. **Ít gãy hơn về mặt cấu trúc.** |
| **Bắt buộc thẻ Visa/Master bật thanh toán quốc tế.** Đây là rào cản lớn nhất của họ với tệp U45+, phải xử lý bằng cả một FAQ dài + phương án khóa tạm. | DeepSeek nạp được bằng cách dễ hơn, và **rẻ hơn Claude nhiều lần**. Có thể thiết kế đường vào không cần thẻ quốc tế → **gỡ đúng cái chốt chặn lớn nhất của họ**. |
| **Sản phẩm chỉ làm 1 việc: đăng bài.** Chính họ phải viết "chuỗi này đăng bài, nó không bán hàng thay bạn". | Mây là **trợ lý thường trú có trí nhớ + nhiều kỹ năng** (viết content, tư vấn, đọc web, đọc bài FB/IG/TikTok, tạo ảnh). Không gian nâng cấp rộng hơn hẳn. |
| **Chỉ chạy khi có mặt họ.** Chuỗi n8n cần trainer sửa khi hỏng → mới có PRELA Cloud 686k. | Bạn có **Railway + Docker + `start.sh` tự refresh skill mỗi lần deploy** — mô hình vận hành hộ của bạn rẻ hơn về công. |
| **Slots đang 0/31.** Đợt 23/08 tại thời điểm quét chưa bán được suất nào dù đang chạy ads. | Hoặc họ vừa mở đợt, hoặc CPA đang xấu. Dù sao: **thị trường này chưa bị chiếm**. Bạn còn cửa vào. |
| **Toàn bộ giá trị nằm ở "có người ngồi cùng".** Không nhân bản được — 31 người là trần cứng. | Đây cũng sẽ là trần của bạn. Cần thiết kế sẵn đường thoát trần (xem Phần 6.5). |

---

## PHẦN 6 — Bản đồ dựng hệ tương tự cho Coachio Mây

### 6.1 Định nghĩa chào hàng

| Thành phần | Đề xuất |
|---|---|
| Tên cơ chế | Một cái tên riêng có ™, gọi Mây là **"trợ lý riêng"/"nhân viên số"**, không gọi là "bot" hay "khóa AI" |
| Lời hứa | **"4 tiếng — bạn rời khỏi buổi với một trợ lý AI chạy 24/7 trong Telegram của bạn, biết tên bạn, nhớ việc của bạn."** |
| Nghiệm thu trong buổi | Khách nhắn Telegram → **Mây trả lời** → chụp màn hình. Đây là "khoảnh khắc bài lên page" phiên bản của bạn. |
| Bằng chứng cầm về | ① Bot Telegram đang chạy trên Railway của chính họ ② Ảnh chụp đoạn chat đầu tiên ③ File `SOUL.md`/`USER.md` mang tên họ ④ Bản ghi hình ⑤ Phòng kèm bù |
| Chống phụ thuộc | **Key DeepSeek mang tên họ, Railway mang tài khoản họ, repo GitHub của họ.** Nói thẳng: "Mây sống kể cả khi bạn không còn liên quan gì đến tôi." |
| Backend | ① Vận hành hộ theo tháng (bạn deploy/giám sát/cập nhật engine) ② Gói kỹ năng nâng cao (`jina`, `social-extract`, `coachio-image` — mỗi cái là một "nhân viên" mới) ③ Lộ trình dài |

**Lợi thế lớn nhất bạn có mà họ không có:** sản phẩm của bạn **nói chuyện lại**.
Khoảnh khắc "Mây trả lời tin nhắn đầu tiên và gọi đúng tên tôi" mạnh hơn nhiều so với "một bài đăng lên page".
Toàn bộ trang bán hàng nên xoay quanh **đúng 5 giây đó**.

### 6.2 Bậc thang giá đề xuất

```
Buổi lắp ráp 4 tiếng          399k  (đợt sáng lập, đổi lấy quyền quay màn hình + nhận xét)
                              ↑ giá thật công bố trước: 1.68tr, về đúng giá từ đợt 4
Vận hành hộ                   ~490–690k/tháng   ← doanh thu lặp lại, chỗ kiếm tiền thật
Gói kỹ năng / nhân viên số #2 bán thêm theo món
Lộ trình đầy đủ               399k được trừ hết
```

Giữ nguyên cơ chế **neo hai tầng** và **reason-why đợt sáng lập** — hai thứ này là phần
mạnh nhất trong công thức của họ và hoàn toàn hợp pháp để dùng lại.

### 6.3 Lịch trình 4 tiếng — bản của bạn

Rủi ro: quy trình của bạn hiện có **nhiều bước hơn** của họ (Node/pnpm hoặc Railway + GitHub + BotFather + Getmyid + DeepSeek key + biến môi trường). Phải nén xuống bằng đúng vũ khí bạn đã có: **"câu thần chú"** trong `BAT-DAU.md`.

```
0:00–0:15  Điểm danh, kiểm 5 điều kiện
0:15–0:40  Lấy 3 chìa khoá cùng nhau: DeepSeek key · BotFather token · Telegram ID
           (đây là "chỗ 8/10 người bỏ cuộc" của bạn — làm chung, chia màn hình)
0:40–1:00  CHIẾN THẮNG ĐẦU: bot hiện tên trong Telegram (chưa cần chạy)
1:00–1:45  Deploy Railway bằng câu thần chú — AI làm, khách kiểm chứng
1:45–2:00  Nghỉ
2:00–3:00  🔥 KHOẢNH KHẮC: nhắn Mây → Mây trả lời → đặt tên → cá tính hoá → chụp màn hình
3:00–3:25  Gắn kỹ năng + xử lý 5 lỗi hay gặp (409 Conflict, sai OPENCLAW_HOME, ...)
3:25–3:40  15 phút giới thiệu lộ trình — CÓ ĐỒNG HỒ, ghi rõ trên trang
3:40–4:00  Hỏi đáp mở + ghi tên vào phòng kèm bù
```

Bắt buộc: **"chiến thắng nhỏ" phải rơi vào trước phút 60.** Họ đặt ở 0:35–0:55 (thấy tên page).
Người mất niềm tin trong giờ đầu sẽ không quay lại ở giờ thứ ba.

### 6.4 Landing page — chép khung, không chép chữ

Dùng nguyên khung 26 khối ở Phần 2. Ba khối cần đầu tư nhiều nhất:

- **Khối 04 (máy tính giờ):** phiên bản của bạn nên tính **"bao nhiêu giờ/năm bạn mất vì phải tự làm
  những việc lặp lại"** hoặc **"bao nhiêu tiền/năm bạn trả cho trợ lý part-time"**. Bắt khách bấm.
- **Khối 03 (video chính):** **quay màn hình thật một đoạn chat với Mây.** Đây là tài sản bán hàng
  số 1 của bạn. Không cần đẹp, cần thật.
- **Khối 09 (dưới nắp capo):** liệt kê đúng 6 bộ phận — engine OpenClaw · `SOUL.md`/`USER.md` (trí nhớ &
  tính cách) · `AGENTS.md` (luật làm việc) · thư mục `skills/` · key DeepSeek mang tên bạn · Railway 24/7.
  Bạn đã có sẵn nội dung này trong `README.md`, chỉ cần viết lại cho người không biết code đọc.

### 6.5 Hạ tầng — dựng theo thứ tự này

| Ưu tiên | Hạng mục | Ghi chú |
|---|---|---|
| P0 | **LP tĩnh 1 file + khối `CFG` ở đầu** | Copy đúng triết lý của họ. Sửa giá/ngày/số tài khoản không cần đụng code. |
| P0 | **Form 2 ô (Tên + SĐT) → QR VietQR → nhóm Zalo** | Bỏ email. Mã đơn dạng `XXX` + 4 số cuối SĐT + 3 chữ cái. |
| P0 | **Meta Pixel + đủ bộ event** (Phần 3.4) | Không có đo lường thì không có tối ưu. Làm ngay từ ngày 1. |
| P1 | **Webhook nhận đơn** | n8n self-host như họ, **hoặc** Google Apps Script / Cloudflare Worker nếu muốn nhẹ hơn. Nhớ bật CORS thật và **không dùng `no-cors`**. |
| P1 | **SePay webhook đối soát tự động theo nội dung CK** | Chính xác cơ chế của họ. Rẻ, chạy tốt ở VN. |
| P1 | **Lưới an toàn đơn hàng**: localStorage → retry ×2 → `sendBeacon` → event báo động | Bài học họ đã trả giá, bạn lấy miễn phí. |
| P2 | **API đếm chỗ thật** + quy tắc chỉ hiện khi đã bán ≥ nửa | Trung thực mà vẫn tạo áp lực. |
| P2 | **CAPI server-side Purchase, dedup bằng eventID** | Cần khi bắt đầu scale ads. |
| P3 | **ref/UTM cookie 60 ngày** | Hạ tầng affiliate cho sau này. |
| P3 | **Đường thoát trần 31 người** | Trợ giảng kèm 1:8, hoặc bản "tự lắp có AI kèm" giá thấp hơn. Nghĩ trước khi bị chặn. |

### 6.6 Vận hành theo đợt

```
Tuần 1  Dựng LP + webhook + QR + Pixel. Quay video demo chat với Mây.
        Chốt: ngày đợt 1, sức chứa (đề xuất 20–31), 5–6 điều kiện tham gia.
Tuần 2  Chạy ads nhỏ (200–500k/ngày). Đọc HourCalculator, ScrollDepth, FaqOpen.
        FAQ nào mở nhiều nhất → viết lại khối tương ứng.
Tuần 3  Dạy đợt 1. Bắt buộc: quay màn hình kết quả + xin 1 câu nhận xét NGAY TRONG BUỔI.
        (Không xin sau — sau là mất.)
Tuần 4  Nhét bằng chứng đợt 1 vào khối 13/14. Mở đợt 2. Tăng giá theo cam kết đã ghi.
Hàng tuần  Phòng kèm bù 60 phút, cố định giờ. Đây là chi phí cam kết — và là nơi bán backend.
```

---

## PHẦN 7 — Những gì KHÔNG nên chép

1. **Không chép câu chữ.** Cấu trúc thì tự do, câu chữ là tài sản của họ. Và tệp coach VN nhỏ —
   trùng câu là bị nhận ra trong một ngày.
2. **Không chép các con số thống kê của họ** ("8 trên 10 người bỏ cuộc", "51+ chuỗi đang chạy",
   "360 triệu"). Đó là số của họ. Bạn dùng số của bạn, kể cả khi số của bạn nhỏ hơn.
   *"Đây là đợt đầu tiên"* là một câu bán hàng hợp lệ và mạnh.
3. **Không bật social proof giả.** Họ có sẵn cơ chế mà không dùng — có lý do.
4. **Không hứa kết quả kinh doanh** ("có 7 người nhắn tin sau 15 phút" là **tin nhắn học viên**,
   không phải cam kết của họ — chú ý sự khác biệt đó khi viết). Meta Ads siết rất chặt
   các claim thu nhập; và cam kết sai là rủi ro hoàn tiền thật.
5. **Không cam kết hoàn tiền khi chưa tính được chi phí.** Cam kết 3 lớp của họ rẻ vì kết quả
   nghiệm thu được trong buổi và vì có điều kiện "phải vào phòng kèm bù ít nhất một lần".
   Nếu sản phẩm của bạn không nghiệm thu được trong buổi, đừng chép cam kết này.
6. **Không mở bán khi chưa có backend.** Không có doanh thu lặp lại thì 399k × 31 không nuôi nổi ads.

---

## PHẦN 8 — Việc cần làm tiếp

- [ ] Chốt tên cơ chế ™ và một câu lời hứa duy nhất cho Mây
- [ ] Quay video demo: nhắn Telegram → Mây trả lời → đặt tên → cá tính hoá (2 phút, màn hình thật)
- [ ] Dựng LP 26 khối theo khung Phần 2, có khối `CFG` (giá/ngày/số TK/deadline/sức chứa)
- [ ] Máy tính giờ ở khối 04 — chọn đúng đơn vị đau của tệp bạn
- [ ] Webhook nhận đơn + QR VietQR + đối soát SePay + lưới an toàn 3 lớp
- [ ] Meta Pixel + đủ bộ custom event + CAPI dedup
- [ ] Viết checklist 5–6 điều kiện tham gia (gửi trước buổi 48h trong nhóm Zalo/Telegram)
- [ ] Rút gọn quy trình cài đặt xuống mức "câu thần chú" — đo thử: người không biết code mất bao lâu?
- [ ] Chốt giá gói vận hành hộ theo tháng **trước khi** mở bán đợt 1

---

*Tài liệu phân tích nội bộ. Dữ liệu quét ngày 12/08/2026 từ nguồn công khai.*
