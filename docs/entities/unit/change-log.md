# Change Log — Unit + UnitConversion

## v1.3 — 2026-08-11

**Refactor lớn: `conversion_type` + reverse virtual + gộp response + partial unique + hard delete.**

| # | Thay đổi | Lý do |
|---|---|---|
| 1 | `Unit.conversion_type`: field mới (`global` / `material`) | Mỗi đơn vị chỉ thuộc 1 loại. Tránh trộn lẫn. |
| 2 | Ràng buộc `material` trên `UnitConversion` theo `Unit.conversion_type` | Global → material phải null. Material → material bắt buộc có. |
| 3 | Reverse virtual: query `conversions_to` + tính `1/factor` cho global | Không lưu DB row dư thừa. Material-specific không reverse. |
| 4 | `isReverse` field trên response | FE phân biệt direct vs reverse. Dùng `id` thật để PUT/PATCH. |
| 5 | Gộp `globalConversions` + `materialConversions` → 1 list `conversions` | Với `conversion_type`, response chỉ chứa 1 loại. |
| 6 | Bỏ `scope` field trên `UnitConversionSerializer` | Thông tin này giờ nằm ở `Unit.conversionType`. |
| 7 | `GET /api/units/{id}/` gộp conversions (bỏ endpoint `/conversions/` GET) | Detail đã trả `DetailedUnitSerializer`, không cần endpoint riêng. |
| 8 | Permission: giữ `IsAdminOrStorekeeper` | Thủ kho vẫn cần toàn quyền catalog. |
| 9 | `_format_factor()`: strip trailing zeros (`"500.0000"` → `"500"`) | Response sạch hơn, FE không cần parse trailing zeros. |
| 10 | Partial `UniqueConstraint` thay thế constraint cũ | SQL NULL ≠ NULL → partial unique index với `condition` giải quyết triệt để. |
| 11 | Cấm reverse pair cho global (`TAN→KG` đã có → từ chối `KG→TAN`) | API đã có reverse virtual, tạo chiều ngược gây trùng lặp. |
| 12 | Validate uniqueness trong serializer (thay cho IntegrityError 500) | Trả 400 + message rõ ràng thay vì crash 500. |
| 13 | `DELETE /api/unit-conversions/{id}/` → hard delete + 200 + object | Client nhận object vừa xóa để cập nhật local state. |
| 14 | `DELETE /api/unit-conversions/{id}/` bỏ soft delete | UnitConversion là mapping đơn giản, không cần audit trail. |

---

## v1.2 — 2026-08-07

Thiết kế ban đầu trong [`docs/entities/material/`](../material/change-log.md).

## v1.1 — 2026-08-07

Permission: IsAdmin → IsAdminOrStorekeeper.

## v1.0 — 2026-08-05

Khởi tạo cùng Material trong app `catalog`.
