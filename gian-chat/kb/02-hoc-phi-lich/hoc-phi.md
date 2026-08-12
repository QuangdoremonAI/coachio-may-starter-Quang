---
chu_de: học phí các chương trình
tra_loi_cho: "học phí", "bao nhiêu tiền", "giá", "đóng mấy lần", "trả góp", "có giảm không", "ưu đãi", "học bổng", "hoàn tiền"
cap_nhat: <<< ĐIỀN NGÀY >>>
---

> 🔒 **FILE NÀY LÀ DANH SÁCH TRẮNG VỀ TIỀN.**
>
> Code quét file này lấy mọi con số tiền. Bot nói ra con số **không có ở đây**
> thì bị chặn tự động. Nghĩa là bot **không thể bịa giá** — kể cả khi model lú,
> kể cả khi khách dụ.
>
> Hệ quả ngược lại: **file này trống thì bot không nói được con số nào cả.**
> Điền đầy đủ, kể cả các mức trả góp và ưu đãi.

## Bảng học phí

| Chương trình | Học phí | Ghi chú |
|---|---|---|
| CCSC | <<< ĐIỀN: ví dụ 15.000.000đ >>> | <<< ĐIỀN >>> |
| CEO Kiến Tạo | <<< ĐIỀN >>> | <<< ĐIỀN >>> |
| Công Thức Rung | <<< ĐIỀN >>> | <<< ĐIỀN >>> |
| Tư vấn 1-1 | <<< ĐIỀN >>> | <<< ĐIỀN >>> |
| Combo (nếu có) | <<< ĐIỀN >>> | <<< ĐIỀN >>> |

## Cách đóng

<<< ĐIỀN: đóng một lần hay nhiều đợt, mỗi đợt bao nhiêu, deadline từng đợt.
Nhớ ghi ĐỦ CON SỐ — số nào không ghi ở đây thì bot không nói được. >>>

## Ưu đãi đang áp dụng

<<< ĐIỀN: mức ưu đãi + điều kiện + HẠN CHÓT.
⚠️ Ưu đãi hết hạn thì phải xoá khỏi file này và deploy lại, nếu không bot
vẫn nói tiếp. Đặt nhắc lịch cho việc này. >>>

## Chính sách hoàn tiền

<<< ĐIỀN: có hay không, điều kiện gì, trong bao nhiêu ngày.
Nếu KHÔNG hoàn tiền thì viết rõ "không hoàn tiền" — bot cần biết để trả lời
thẳng thay vì né. >>>

## Bot được nói gì về giá

- Được: đọc đúng con số trong bảng trên.
- Được: giải thích học phí gồm những gì.
- **Không được**: giảm giá, hứa ưu đãi riêng, "để em xin anh Quang", gợi ý
  mặc cả, so sánh giá với đối thủ.

Khách đòi giảm → bot nói học phí là cố định, rồi mời để lại số để trao đổi
trực tiếp về phương án đóng.
