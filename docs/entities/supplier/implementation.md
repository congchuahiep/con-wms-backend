# Implementation Checklist — Supplier

## Cấu hình

- [x] Tạo Django app: `python manage.py startapp supplier`
- [x] Thêm `"supplier"` vào `INSTALLED_APPS` trong `config/settings.py`

## Model

- [x] `supplier/models.py`: định nghĩa model `Supplier` (12 fields)
  - `code` CharField(20) unique
  - `name` CharField(200)
  - `tax_code` CharField(20) unique, blank
  - `contact_person` CharField(100) blank
  - `phone` CharField(20) blank
  - `email` EmailField blank
  - `address` TextField blank
  - `note` TextField blank
  - `is_active` BooleanField default=True
  - `created_at`, `updated_at` DateTimeField auto
- [x] `__str__` method: `f"{self.code} — {self.name}"`
- [x] `Meta`: `db_table = "supplier"`, `verbose_name` / `verbose_name_plural`
- [x] `supplier/admin.py`: đăng ký model với `@admin.register(Supplier)`
- [x] Chạy `python manage.py makemigrations supplier` + `migrate`

## Serializers

- [x] `supplier/serializers.py`: `SupplierSerializer(ModelSerializer)`
  - Fields explicit: id, code, name, tax_code, contact_person, phone, email, address, note, is_active, created_at, updated_at
  - `read_only_fields`: id, created_at, updated_at

## Views

- [x] `supplier/views.py`: `SupplierViewSet(ModelViewSet)`
  - `queryset`: `Supplier.objects.all().order_by("code")`
  - `filter_backends`: `SearchFilter` (search code, name) + `DjangoFilterBackend` (filter is_active)
  - `get_permissions()`: Read → `IsAuthenticated`, Write → `IsAdmin`
  - `perform_destroy()`: soft delete — set `is_active=False`
  - `@extend_schema` + `@extend_schema_view` cho drf-spectacular
- [x] `supplier/filters.py`: `SupplierFilter(FilterSet)` — filter `is_active`, custom search `code` + `name`

## URLs

- [x] `supplier/urls.py`: `DefaultRouter` register `suppliers` với `SupplierViewSet`
- [x] Include vào `config/urls.py`: `path("api/", include("supplier.urls"))` → URL cuối: `/api/suppliers/`

## Permissions

- [x] Không cần file `supplier/permissions.py` mới — dùng lại `iam.permissions.IsAdmin`
- [x] Import: `from iam.permissions import IsAdmin`

## Tests

- [x] `supplier/tests.py`: 8 tests
  - Test GET list unauthenticated → 401
  - Test GET list authenticated → 200
  - Test POST admin → 201
  - Test POST storekeeper → 403
  - Test PUT admin → 200
  - Test PUT storekeeper → 403
  - Test DELETE admin → 204 (soft delete)
  - Test DELETE storekeeper → 403
- [x] Chạy `python manage.py test supplier` — 8/8 OK

## Seed Data

- [x] `supplier/management/commands/seed_suppliers.py`: 2 NCC mẫu

| code | name | tax_code | contact_person | phone |
|---|---|---|---|---|
| `NCC001` | Công ty TNHH Vật Liệu Xây Dựng ABC | 0123456789 | Anh Tuấn — quản lý bán hàng | 0903123456 |
| `NCC002` | Đại lý Sắt Thép Miền Tây | 0987654321 | Chị Hương | 0918123456 |

- [x] Chạy `python manage.py seed_suppliers` — 2 NCC đã tạo

## Tài liệu

- [x] Cập nhật `docs/entities/README.md` — trạng thái Supplier: ✅ Done
- [x] Cập nhật `docs/entities/supplier/change-log.md` — checklist done
