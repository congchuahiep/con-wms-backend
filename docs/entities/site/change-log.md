# Change Log — Site (Công Trường)

## v0.1 — 2026-08-18 (Thiết kế)

Thiết kế entity Công trường, các quyết định chốt với user:

| Quyết định | Nguồn |
|---|---|
| Tạo hẳn entity `Site` thay vì free text `destination` | User 2026-08-18: "Giờ để đỡ cái việc destination thì nên tạo model Site luôn nhỉ?" — kết hợp user xác nhận trước đó "sau này sẽ có Model Công trường" |
| `OutboundNote.site` FK bắt buộc khi `issue_for_use` | Thay cho `destination` trong thiết kế outbound v0.1 (xem [`../outbound-note/change-log.md`](../outbound-note/change-log.md) v0.2) |
| `InboundNote` (trả lại từ công trường) có link Site không | ✅ **Có** — user chốt 2026-08-18: "Chắc là cũng phải thêm Site vào InboundNote nhỉ?". `site` FK bắt buộc khi `return_from_site`, null khi purchase (xem [`../inbound-note/model.md`](../inbound-note/model.md) D13) |
| App `sites` (số nhiều) — tránh shadowing module chuẩn `site` | D5 |
| Master data: write `IsAdmin`, read `IsAuthenticated`, soft delete `is_active` | Theo chuẩn Warehouse/Supplier |
| Không GPS, không phân trang | Giống Warehouse — YAGNI, master data |

### Kết quả validate Context7

Pattern giống hệt Warehouse/Supplier (đã validate trong change-log của 2 entity đó): model đơn giản + `ModelViewSet` + `IsAdmin` — không cần pattern Django/DRF mới nào.

### Trạng thái

📝 **Chờ user duyệt — chưa code** (entity-workflow Bước 3). Code theo checklist trong [`implementation.md`](implementation.md).
