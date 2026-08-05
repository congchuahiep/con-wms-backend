# Implementation Checklist — Warehouse

## Cấu hình

- [x] Tạo Django app: `python manage.py startapp warehouse`
- [x] Thêm `"warehouse"` vào `INSTALLED_APPS` trong `config/settings.py`

## Model

- [x] `warehouse/models.py`: định nghĩa model `Warehouse` (9 fields)
  - `code` CharField(20) unique
  - `name` CharField(200)
  - `address` TextField blank *(địa chỉ kho)*
  - `note` TextField blank *(ghi chú về bản thân kho: tình trạng, lưu ý quản lý)*
  - `latitude` DecimalField(9,6) null, blank
  - `longitude` DecimalField(9,6) null, blank
  - `is_active` BooleanField default=True
  - `created_at`, `updated_at` DateTimeField auto
- [x] `__str__` method: `f"{self.code} — {self.name}"`
- [x] `warehouse/admin.py`: đăng ký model với `@admin.register(Warehouse)`
- [x] Chạy `python manage.py makemigrations warehouse` + `migrate`

## Serializers

- [x] `warehouse/serializers.py`: `WarehouseSerializer(ModelSerializer)`
  - Fields explicit: id, code, name, address, note, latitude, longitude, is_active, created_at, updated_at
  - `read_only_fields`: id, created_at, updated_at
  - Validation: `code` uppercase, không chứa ký tự đặc biệt *(bỏ qua — không cần thiết cho quy mô nhỏ)*

## Views

- [x] `warehouse/views.py`: `WarehouseViewSet(ModelViewSet)`
  - `queryset`: `Warehouse.objects.all().order_by("name")` — trả về tất cả, filter active qua `?is_active=true`
  - `filter_backends`: `SearchFilter` (search code, name) + `DjangoFilterBackend` (filter is_active)
  - `get_permissions()`: Read → `IsAuthenticated`, Write → `IsAdmin`
  - `perform_destroy()`: soft delete — set `is_active=False`
  - `@extend_schema` + `@extend_schema_view` cho drf-spectacular
- [x] `warehouse/filters.py`: `WarehouseFilter(FilterSet)` — filter `is_active`, custom search `code` + `name`

## URLs

- [x] `warehouse/urls.py`: `DefaultRouter` register `warehouses` với `WarehouseViewSet`
- [x] Include vào `config/urls.py`: `path("api/", include("warehouse.urls"))` → URL cuối: `/api/warehouses/`

## Permissions

- [x] Không cần file `warehouse/permissions.py` mới — dùng lại `iam.permissions.IsAdmin`
- [x] Import: `from iam.permissions import IsAdmin`

## Tests

- [x] `warehouse/tests.py`: 8 tests — tất cả pass
  - Test GET list unauthenticated → 401
  - Test GET list authenticated → 200
  - Test POST admin → 201
  - Test POST storekeeper → 403
  - Test PUT admin → 200
  - Test PUT storekeeper → 403
  - Test DELETE admin → 204 (soft delete)
  - Test DELETE storekeeper → 403
- [x] Chạy `python manage.py test warehouse` — 8/8 OK

## Seed Data

- [x] `warehouse/management/commands/seed_warehouses.py`: 2 kho mẫu

| code | name | note |
|---|---|---|
| `KHO_CHINH` | Kho chính — Bãi sau | Kho chính — nền bê tông, mái tôn, có cửa cuốn |
| `KHO_PHU` | Kho phụ — Gần cổng | Kho phụ — nền đất, che bạt, chỉ chứa vật liệu nhẹ |

- [x] Chạy `python manage.py seed_warehouses` — 2 kho đã tạo

## Tài liệu

- [x] Cập nhật `docs/entities/README.md` — trạng thái Warehouse: ✅ Done
- [ ] Cập nhật `docs/entities/warehouse/change-log.md` — v1.3 checklist done
- [ ] Cập nhật `docs/PROJECT_CHARTER.md` §5.1 F3 — điều chỉnh mô tả Location cho khớp thực tế
