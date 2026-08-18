# ADR-0001: Sổ kho (Stock Movement Ledger) thay vì bảng tồn kho ghi đè

- **Ngày:** 2026-08-13
- **Trạng thái:** Đã chốt (user duyệt 5/5)
- **Liên quan:** `docs/entities/stock/`, `docs/entities/inbound-note/`

## Bối cảnh

Câu hỏi kiến trúc cốt lõi: **"Khi tạo phiếu nhập, tồn kho sinh ra như thế nào? Xóa phiếu thì sao? Có cần trace-back không?"**

Hai lựa chọn:

1. **Bảng tồn ghi đè** (`MaterialStock`): mỗi (kho, vật tư) 1 dòng, `quantity` cộng/trừ trực tiếp khi tạo/xóa phiếu.
2. **Sổ kho** (`StockMovement`): mọi sự kiện nhập/xuất/điều chỉnh là 1 dòng ghi bất biến; tồn = `SUM(quantity)` các dòng.

## Quyết định

**Chọn sổ kho (phương án 2).** Tồn kho là con số *tính ra*, không phải con số *lưu sẵn* — giống "số dư ngân hàng" được cộng trừ từ các giao dịch, không ai sửa tay số dư.

## Lý do

| Tiêu chí | Bảng tồn ghi đè | Sổ kho |
|---|---|---|
| Sửa phiếu đã chốt | Lệch tồn — phải trừ lại tay, dễ sai | Cấm sửa; hủy = dòng ngược dấu, luôn khớp |
| Trace-back (NCC, giá, ngày, người lập) | Không có — mất lịch sử | Mỗi dòng trỏ về phiếu nguồn |
| Báo cáo Nhập–Xuất–Tồn theo kỳ (F5) | Không thể — chỉ có số cuối | Tổng theo `date` trong khoảng |
| Giá trị tồn "giá nhập gần nhất" (F5) | Phải chép giá vào bảng tồn | Query dòng `inbound_purchase_from_supplier` mới nhất |
| Audit cho kế toán (NFR log thao tác) | Phải log riêng | Sổ kho chính là log |
| Hiệu năng (quy mô ~10 người, vài trăm vật tư) | Nhanh hơn chút | Aggregate có index, chạy trong ms — không phải vấn đề |

## Hệ quả thiết kế

1. `StockMovement` **bất biến**: không update, không delete, không API write trực tiếp (kể cả admin).
2. Mọi thay đổi tồn phải đi qua **phiếu**: chốt phiếu = ghi dòng (+/−), hủy phiếu = dòng ngược dấu (`reversal_of`) + lý do bắt buộc.
3. Phiếu có vòng đời `draft → posted → voided`; phiếu đã chốt bất biến.
4. Bảng cache tồn chỉ thêm nếu sau này query chậm ở quy mô lớn — YAGNI hiện tại.
5. Cột `lot` chừa sẵn (nullable) cho trace theo lô (future scope, charter §5.3).
