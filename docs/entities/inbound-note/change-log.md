# Change Log — Inbound Note

## v2.3 — 2026-08-18

Enum gom vào model + đổi semantics `total_quantity` (xem stock v1.4):

- `NoteType` → `InboundNote.Type`, `NoteStatus` → `BaseNote.Status` (nested enum, validate Context7 ✅)
- Label `noteType` đổi: "Nhập mua" → "Mua hàng từ nhà cung cấp"; "Nhập hàng công trường trả lại" → "Công trường trả lại hàng" — cập nhật ví dụ `noteTypeLabel` trong `api.md` + `frontend-migration.md`
- `total_quantity` = **số dòng vật tư** (integer) — user chốt; test `test_create_draft_storekeeper` kỳ vọng `1`, docs `api.md` cập nhật kèm ghi chú
- Field table: `note_type` ghi rõ `purchase` / `return_from_site`; `date` verbose "Ngày nghiệp vụ"

## v2.2 — 2026-08-18

Refactor `BaseNote` (xem stock v1.3):

- `InboundNote` kế thừa abstract base `BaseNote` — bỏ 12 field trùng lặp, giữ `note_type` + `supplier`
- Vòng đời chốt/hủy dời từ `services.py` vào `BaseNote.post()` / `BaseNote.void()`, `InboundNote` chỉ viết 2 hook sinh dòng sổ kho
- `views.py` / seed command gọi trực tiếp `note.post()` / `note.void()`; `services.py` chỉ còn sinh số phiếu
- Migration 0004 + 0005 (đổi tên index `ix_inbound_note_*` → `ix_inboundnote_*`, đổi verbose `date` → "Ngày nghiệp vụ")

## v2.1 — 2026-08-14

Đổi tên `NoteType` cho minh bạch (cùng đợt với stock v1.2):

| Thay đổi | Lý do |
|---|---|
| `NoteType.RETURN` → `RETURN_FROM_SITE` (giá trị `return` → `return_from_site`, label "Nhập mua hoàn trả" → "Nhập hàng công trường trả lại") | "Nhập hoàn trả" / `return` gây nhầm lẫn — đọc như trả hàng cho NCC (là xuất kho), trong khi nghiệp vụ là công trường trả hàng về kho |
| Migration `0003` đổi dữ liệu `note_type` cũ → mới | Giữ dữ liệu hiện có nguyên vẹn |
| Cập nhật validate message serializer + seed command + tests | Đồng bộ terminology |
| Ghi chú cho frontend: [`../stock/frontend-migration.md`](../stock/frontend-migration.md) | Hướng dẫn FE thay hằng số enum cũ → mới |

## v2.0 — 2026-08-13

Thiết kế lại vòng đời phiếu sau thảo luận kiến trúc tồn kho (xem ADR-0001, entity [`stock/`](../stock/)):

| #   | Thay đổi                                        | Lý do                                                                                                            |
| --- | ----------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| 1   | `is_active` → `status` (`draft/posted/voided`)  | Phiếu nháp chưa đụng tồn, xóa cứng được; phiếu đã chốt chỉ được hủy (void), không xóa — tránh lệch tồn, giữ audit |
| 2   | Thêm `voided_by`, `voided_at`, `void_reason`    | Log ai hủy, khi nào, lý do (bắt buộc) — đáp ứng NFR "log thao tác quan trọng"                                   |
| 3   | Thêm 2 action: `POST /{id}/post/`, `POST /{id}/void/` | Chốt = ghi sổ kho (+tồn); hủy = ghi dòng ngược dấu (−tồn). Không có API sửa tồn tay                                |
| 4   | PUT/DELETE chỉ áp dụng cho `draft`              | Phiếu đã chốt bất biến — sửa sai = hủy + lập phiếu mới (user chốt)                                                |
| 5   | Giải quyết 2 câu hỏi treo từ v1.0               | "DELETE phiếu" → thủ kho + admin, chỉ draft; "replace-all" → giữ nguyên, chỉ draft                              |

### Kết quả validate Context7

| Library | Kết quả |
|---|---|
| Django 6.0 | ✅ `TextChoices` cho status, FK PROTECT, `transaction.atomic` — đúng pattern |
| DRF | ✅ `@action(detail=True, methods=["post"])` cho post/void — đúng best practice |

### Triển khai (2026-08-13)

- ✅ App `inventory`: InboundNote + InboundNoteLine + StockMovement, migration OK
- ✅ Vòng đời draft → posted → voided hoạt động (chốt ghi sổ kho, hủy ghi ngược dấu)
- ✅ 31 tests — 31/31 pass
- ✅ Seed 2 phiếu mẫu (tự chốt), tồn kho mẫu đúng
- ✅ Dev từ route collision `/api/stock/movements/` — dùng prefix `stock/movements` + `path("stock/")` thủ công

## v1.0 — 2026-08-13

Khởi tạo thiết kế ban đầu:

- 2 models: InboundNote (phiếu) + InboundNoteLine (dòng vật tư)
- `unit_price` trên InboundNoteLine — giá thực tế từng lần nhập, tự nhiên tạo lịch sử giá
- **Không** tạo bảng Supplier-Material (theo PROJECT_CHARTER F2: tự tổng hợp từ phiếu nhập)
- 2 loại phiếu: purchase (có supplier) / return (không supplier)
- Số phiếu auto-generate: `PN-YYYYMMDD-NNN`
- Nested write 1 request (phiếu + dòng) với transaction.atomic
- Permission: thủ kho tạo/sửa (IsAdminOrStorekeeper), admin xóa (IsAdmin)

### Kết quả validate Context7

| Library | Kết quả |
|---|---|
| Django 6.0 | ✅ FK PROTECT/CASCADE, DecimalField precision, TextChoices, DateField — đúng pattern |
| DRF | ✅ Writable nested serializer: override `create()`/`update()` với `transaction.atomic` — đúng best practice |
