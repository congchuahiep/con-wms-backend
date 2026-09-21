# Change Log — Site (Công Trường)

## v0.1 — 2026-08-18 (Thiết kế)

Thiết kế entity Công trường, các quyết định chốt với user:

| Quyết định                                                                    | Nguồn                                                                                                                                                                                                               |
| ----------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Tạo hẳn entity `Site` thay vì free text `destination`                         | User 2026-08-18: "Giờ để đỡ cái việc destination thì nên tạo model Site luôn nhỉ?" — kết hợp user xác nhận trước đó "sau này sẽ có Model Công trường"                                                               |
| `OutboundNote.site` FK bắt buộc khi `issue_for_use`                           | Thay cho `destination` trong thiết kế outbound v0.1 (xem [`../outbound-note/change-log.md`](../outbound-note/change-log.md) v0.2)                                                                                   |
| `InboundNote` (trả lại từ công trường) có link Site không                     | ✅ **Có** — user chốt 2026-08-18: "Chắc là cũng phải thêm Site vào InboundNote nhỉ?". `site` FK bắt buộc khi `return_from_site`, null khi purchase (xem [`../inbound-note/model.md`](../inbound-note/model.md) D13) |
| App `sites` (số nhiều) — tránh shadowing module chuẩn `site`                  | D5                                                                                                                                                                                                                  |
| Master data: write `IsAdmin`, read `IsAuthenticated`, soft delete `is_active` | Theo chuẩn Warehouse/Supplier                                                                                                                                                                                       |
| Không GPS, không phân trang                                                   | Giống Warehouse — YAGNI, master data                                                                                                                                                                                |

### Kết quả validate Context7

Pattern giống hệt Warehouse/Supplier (đã validate trong change-log của 2 entity đó): model đơn giản + `ModelViewSet` + `IsAdmin` — không cần pattern Django/DRF mới nào.

### Trạng thái

✅ **Đã triển khai** (bản v0.1) — xem [`../site-warehouse/`](../site-warehouse/README.md) cho thiết kế bổ sung v1.1: **mỗi công trường tự động tạo 1 kho liên kết** (auto-create khi tạo Site).

## v1.2 — 2026-09-20 (BREAKING: `is_active` → `status` enum)

Kèm tính năng **Định mức vật tư công trường** (xem [`../site-material-requirement/`](../site-material-requirement/README.md)):

- **`Site.status`** enum (`active` / `completed` / `inactive`) thay thế `is_active` (bool) — user chốt "phải dùng trạng thái enum cho đúng đắn". Migration dữ liệu: `is_active=True → active`, `False → inactive`.
- Thêm `settled_at` / `settled_by` (chỉ có khi `status=completed` — qua **Tất toán**).
- API **breaking**:
  - Response site: bỏ `isActive`, thêm `status` + `statusLabel` + `settledAt` + `settledBy`.
  - Filter danh sách: `?status=active|completed|inactive|all` (mặc định `active`) thay `?is_active=`.
  - `DELETE /api/sites/{id}/` vẫn soft-delete nhưng đặt `status=inactive`.
- `GET/PUT /api/sites/{id}/requirements/` — bảng so sánh định mức vs tồn kho + bulk replace định mức.
- `POST /api/sites/{id}/settle/` — tất toán (đóng công trường + kho).
