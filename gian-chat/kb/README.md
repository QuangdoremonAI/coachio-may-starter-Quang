# 📚 Knowledge base của Bé Giản

Đây là **bộ não** của bot. Code chỉ là cái máy — cái quyết định bot trả lời
hay hay dở nằm hết ở thư mục này.

> **Nguyên tắc số 1:** bot trả lời sai thì **sửa ở đây trước**, sửa prompt sau.
> 90% lỗi là do knowledge base thiếu, không phải do prompt dở.

---

## Cách viết một file

### 1. Mỗi file mở đầu bằng 3 dòng metadata

```markdown
---
chu_de: học phí CEO Kiến Tạo
tra_loi_cho: "bao nhiêu tiền", "học phí", "giá", "đóng mấy lần", "trả góp"
cap_nhat: 2026-08-12
---
```

- `chu_de` — một cụm ngắn, nói file này về cái gì.
- `tra_loi_cho` — **các câu khách hay hỏi, viết đúng như khách gõ**.
  Dòng này được cộng điểm gấp đôi khi tìm kiếm, nên viết kỹ.
- `cap_nhat` — ngày sửa gần nhất. Không có ngày thì 6 tháng sau không ai
  biết con số còn đúng không.

### 2. Cắt bằng heading `##`

Mỗi `##` là một đoạn riêng khi bot đi tìm. Một ý một heading.
Đoạn lý tưởng **200–350 từ**. Dài hơn 400 từ là bot trả lời cụt.

### 3. Viết bằng giọng nói, không phải giọng brochure

❌ *"Chương trình được thiết kế bài bản nhằm mang đến giá trị vượt trội…"*
✅ *"Khoá này dành cho chủ doanh nghiệp 20–200 nhân sự, đang thấy tháng nào
cũng có đơn mà cuối tháng không còn tiền."*

**Bot copy giọng của knowledge base.** Viết brochure thì bot nói giọng brochure.

### 4. Số liệu phải có nguồn và ngày

Không có ngày → bot nói số cũ hai năm trước mà chẳng ai biết.

---

## Thư mục nào chứa gì

| Thư mục | Nội dung |
|---|---|
| `00-nguoi-va-he/` | Anh Quang là ai, hệ tư tưởng gồm những gì |
| `01-san-pham/` | Từng chương trình: cho ai, học gì, bao lâu, ra kết quả gì |
| `02-hoc-phi-lich/` | **Nguồn sự thật duy nhất về tiền và lịch** |
| `03-cau-hoi-thuong-gap/` | FAQ thật, chép từ inbox |
| `04-cau-chuyen/` | Case học viên có số liệu |
| `05-ranh-gioi/` | Những gì bot không được nói |

---

## ⚠️ Về file học phí

`02-hoc-phi-lich/hoc-phi.md` không chỉ là tài liệu — nó là **danh sách trắng**.

Code quét file này lấy mọi con số tiền. Bot nói ra con số **không có trong đó**
thì bị chặn ngay, thay bằng "để em gửi bảng giá chính thức". Nghĩa là bot
**không thể bịa giá**, kể cả khi model có lú.

Hệ quả: file này trống thì bot **không nói được bất kỳ con số tiền nào**.

---

## Lấy nội dung ở đâu nhanh nhất

Xuất 500 tin nhắn inbox Facebook/Zalo gần nhất → nhóm lại 30 câu hỏi lặp
nhiều nhất → **đó chính là file `faq-truoc-khi-mua.md`**.

Nhanh hơn ngồi nghĩ 10 lần, và đúng ngôn ngữ khách thật đang dùng.

---

## Kiểm tra trước khi deploy

```bash
python scripts/check_kb.py
```

Báo cho anh: file nào còn `<<< ĐIỀN >>>`, file nào thiếu metadata, đoạn nào
dài quá, bảng giá đã có chưa.

File nào còn nhiều chỗ `<<<` chưa điền thì **bot bỏ qua luôn file đó** —
thà không biết còn hơn nói bậy.
