# Change Log — Warehouse Entity

## v1.4 — 2026-08-01

Triển khai code hoàn chỉnh:

| # | Thay đổi | Lý do |
|---|---|---|
| 1 | Tạo Django app `warehouse`, model 9 fields, migration | |
| 2 | `WarehouseViewSet(ModelViewSet)` + `SearchFilter` + `WarehouseFilter` | Theo pattern `AuthViewSet`; filter `is_active`, search `code` + `name` |
| 3 | Soft delete qua `perform_destroy()` — set `is_active=False` | Không xóa cứng kho đã có dữ liệu |
| 4 | `@extend_schema` + `@extend_schema_view` cho toàn bộ action | drf-spectacular Swagger UI |
| 5 | `seed_warehouses` command — 2 kho mẫu | |
| 6 | 8 tests (CRUD + permissions) — all pass | |

## v1.3 — 2026-08-01

Sửa ngữ nghĩa `note` field:

| # | Thay đổi | Lý do |
|---|---|---|
| 1 | `note` không còn mang nghĩa "vị trí đặt đồ" — đổi thành "ghi chú chung về kho" | `note` trên Warehouse là ghi chú về bản thân kho (tình trạng, lưu ý quản lý). Vị trí đặt đồ thuộc về entity `MaterialStock` (tồn kho theo vật tư) hoặc `Location` (tương lai), không phải Warehouse. |

## v1.2 — 2026-08-01

Bổ sung sau khi thảo luận với user:

| # | Thay đổi | Lý do |
|---|---|---|
| 1 | Thêm `latitude`, `longitude` (DecimalField 9,6; nullable) | Frontend dùng Google Maps chọn vị trí kho trên bản đồ, hiển thị marker. Lưu tọa độ GPS cho phép xem vị trí các kho trên 1 bản đồ. |
| 2 | Cập nhật `PROJECT_CHARTER.md` — "LAN" → "Cloud VPS" | Thực tế các kho cách nhau ~10km, không thể dùng chung LAN. Cần internet để kết nối. Cloud VPS là giải pháp đơn giản nhất. |

## v1.1 — 2026-08-01

Validate thiết kế với Context7 (Django 6.0 + DRF) — không thay đổi gì, thiết kế hợp lệ:

| # | Tham chiếu | Kết quả |
|---|---|---|
| 1 | Django 6.0 `TextChoices` pattern | Không cần enum cho Warehouse — không có field cần choices |
| 2 | DRF `ModelViewSet` + `DefaultRouter` | Theo đúng pattern của `AuthViewSet` đã làm |
| 3 | DRF `ModelSerializer` | 1 serializer dùng chung list/detail/create/update — đúng best practice |
| 4 | Django `ForeignKey("self")` recursive relationship | Đã dự trù cho Location tương lai, không code ngay |

## v1.0 — 2026-08-01

Khởi tạo: chỉ có Warehouse, không có Location. Lý do:

- Thực tế kho là bãi chứa vật liệu (~200m2), không có kệ/khu vực cố định.
- 1–3 kho, 50–100 SKU, công ty ~10 người.
- Áp dụng YAGNI: không code Location khi chưa cần.
- `note` field cho phép ghi chú vị trí tự do mà không ép cấu trúc.
- Vị trí đặt đồ sẽ được lưu ở entity `MaterialStock` (tồn kho theo vật tư) hoặc `Location` (tương lai).
