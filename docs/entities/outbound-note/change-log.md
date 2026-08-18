# Change Log — Outbound Note

## v0.1 — 2026-08-18 (Thiết kế)

Thiết kế phiếu xuất, các quyết định chốt với user:

| Quyết định | Nguồn |
|---|---|
| 1 phiếu = 1 kho đích — `to_warehouse` trên phiếu (D2) | User 2026-08-18: "1 phiếu = 1 kho đích thế thôi" |
| `destination` free text, tương lai đổi FK → `Site` (D3) | User: "dự án có nhận báo cáo công trường, sau này sẽ có Model Công trường" |
| Chặn cứng tồn âm khi chốt (D4) | User: "làm gì có việc xuất hàng từ kho mà hàng âm" |
| Transfer = 1 phiếu → 2 dòng sổ kho (D5) | Kiến trúc "chứng từ ≠ dòng sổ kho" (ADR-0001) |
| Không có đơn giá (D1) | Nhất quán stock D5 |
| Permission: đọc `IsAuthenticated`, ghi/chốt/hủy `IsAdminOrStorekeeper` | User OK — theo InboundNote |
| App `inventory`, kế thừa `BaseNote` | User OK — gộp vào inventory |

### Kết quả validate Context7

| Library | Kết quả |
|---|---|
| Django 6.0 | ✅ `CheckConstraint` + `Q(...)` cho ràng buộc "đúng 1 nguồn" (3 FK nullable); `AlterField` đổi FK sang nullable OK (SQLite/Postgres — ghi chú Oracle về NULL không liên quan) |
| DRF | ✅ Writable nested serializer (override `create()`/`update()` + `transaction.atomic`); `SerializerMethodField` cho field tính toán; `@action(detail=True)` cho post/void — đúng best practice |

### Trạng thái

📝 **Chờ user duyệt — chưa code** (entity-workflow Bước 3). Code theo checklist trong [`implementation.md`](implementation.md).
