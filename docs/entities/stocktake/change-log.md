# Change Log — Stocktake Note

## v0.2 — 2026-08-18 (Thiết kế) — sửa theo user feedback

**Bỏ snapshot `book_quantity` / `counted_quantity` — phiếu chỉ chứa `difference` + `reason`:**

| Quyết định | Lý do (user 2026-08-18) |
|---|---|
| KHÔNG lưu `book_quantity` snapshot khi tạo phiếu (D1) | Snapshot lưu vào DB sẽ cũ đi khi kho biến động giữa chừng (người khác chốt nhập/xuất) — lưu con số không còn đúng gây hiểu nhầm audit, và luồng "tạo → sửa từng dòng" rườm rà |
| Client gửi thẳng `difference` + `reason` ngay khi tạo phiếu (D2) | Luồng 1 lần: client fetch `/api/stock/` (tồn động, không lưu) → đối chiếu → nhập chênh lệch → tạo phiếu. Không tự sinh dòng cho mọi vật tư |
| Chốt: kiểm tra `difference ≥ −tồn hiện tại` (tính lại lúc chốt) (D4) | Bù an toàn: chặn tồn âm + bắt nhầm dấu/số. Không phụ thuộc snapshot |
| `difference ≠ 0` cho mọi dòng | Dòng lệch 0 không cần ghi — không có khái niệm "dòng chưa đếm" nữa |
| `reason` bắt buộc | NFR log — kế toán cần lý do chênh lệch |

### Kết quả validate Context7

| Library | Kết quả |
|---|---|
| Django 6.0 | ✅ `CheckConstraint` + `Q(...)` cho "đúng 1 nguồn" (3 FK nullable) + `unit_price` ⇔ `inbound_purchase_from_supplier`; `AlterField` đổi FK sang nullable OK; `Sum` aggregate để tính tồn hiện tại lúc chốt |
| DRF | ✅ Writable nested serializer (override `create()`/`update()` + `transaction.atomic`); `@action(detail=True)` post/void — đúng best practice |

### Trạng thái

📝 **Chờ user duyệt — chưa code** (entity-workflow Bước 3). Code theo checklist trong [`implementation.md`](implementation.md).

## v0.1 — 2026-08-18 (Thiết kế)

Thiết kế phiếu kiểm kê, các quyết định chốt với user:

| Quyết định | Nguồn |
|---|---|
| App `inventory` — không tách app `stocktake` (D7) | User 2026-08-18: "gộp vào inventory" |
| `book_quantity` = số trên sổ, hệ thống tự điền lúc tạo phiếu (snapshot) (D1) | Đề xuất ban đầu của agent — **bị user bác bỏ ở v0.2** (xem v0.2 ở trên) |
| Tự sinh dòng cho vật tư tồn ≠ 0, thêm/xóa khi nháp (D2) | Đề xuất của agent — **bỏ ở v0.2**: client tự lấy tồn từ `/api/stock/` |
| Dòng chưa đếm khi chốt → coi như lệch 0 (D3) | Đề xuất của agent — **bỏ ở v0.2**: không còn khái niệm "dòng chưa đếm" |
| Chỉ dòng chênh lệch ≠ 0 ghi sổ, `reason` bắt buộc (D4) | Nhất quán NFR "log thao tác quan trọng" |
| Hủy = đảo dấu dòng điều chỉnh (D6) | Nhất quán ADR-0001 / stock D2 |
| Không có `note_type` (D8) | Chỉ 1 loại phiếu kiểm kê — YAGNI |
| Permission: đọc `IsAuthenticated`, ghi/chốt/hủy `IsAdminOrStorekeeper` | User OK — theo InboundNote |

### Kết quả validate Context7

| Library | Kết quả |
|---|---|
| Django 6.0 | ✅ `CheckConstraint` + `Q(...)` cho "đúng 1 nguồn" (3 FK nullable) + `unit_price` ⇔ `inbound_purchase_from_supplier`; `AlterField` đổi FK sang nullable OK; `Sum` aggregate cho tồn hiện tại |
| DRF | ✅ Writable nested serializer (override `create()`/`update()` + `transaction.atomic`); `SerializerMethodField` tính `difference`; `@action(detail=True)` post/void — đúng best practice |

### Trạng thái

📝 **Chờ user duyệt — chưa code** (entity-workflow Bước 3). Code theo checklist trong [`implementation.md`](implementation.md).
