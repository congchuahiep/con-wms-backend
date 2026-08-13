# Implementation Checklist — Catalog (Material + Category + Unit)

## Cấu hình

- [x] Tạo Django app: `python manage.py startapp catalog`
- [x] Thêm `"catalog"` vào `INSTALLED_APPS` trong `config/settings.py`

## Model

- [x] `catalog/models.py`: định nghĩa 4 model
    - `MaterialCategory` (8 fields, tree: `parent` FK self, `color` CharField nullable)
    - `Unit` (5 fields)
    - `UnitConversion` (7 fields, `from_unit` FK, `to_unit` FK, `material` FK nullable)
    - `Material` (8 fields, `category` FK, `unit` FK)
- [x] `catalog/admin.py`: đăng ký 4 model với `@admin.register`
- [x] Chạy `python manage.py makemigrations catalog` + `migrate`

## Serializers

- [x] `catalog/serializers.py`:
    - `MaterialCategoryTreeSerializer` — nested `children` đệ quy toàn bộ cây (read-only), FK input: `parentId`; output chỉ gồm node gốc (`parent=null`)
    - `MaterialCategoryFlatSerializer` — phẳng, thêm field `depth` (pre-order); dùng khi `?flat=true`
    - `UnitSerializer` — đơn giản
    - `UnitConversionSerializer` — FK input: `toUnitId`, `materialId`; output: nested `toUnit`, `material`; thêm field `scope` ("global" | "material")
    - `MaterialSerializer` — FK input: `categoryId`, `unitId`; output: nested `category`, `unit`

## Views

- [x] `catalog/views.py`:
    - `MaterialCategoryViewSet` — `pagination_class = None`; search `code`, `name`; switch serializer qua query param: mặc định `MaterialCategoryTreeSerializer`, `?flat=true` dùng `MaterialCategoryFlatSerializer`
    - `UnitViewSet` — `pagination_class = None`
        - `@action(detail=True, methods=['get'], url_path='conversions')` → list conversions của unit này
        - `@action(detail=True, methods=['post'], url_path='conversions')` → tạo conversion với `from_unit` = unit này
    - `UnitConversionViewSet` — chỉ PUT + DELETE (GET list + POST create đã có ở UnitViewSet actions)
    - `MaterialViewSet` — paginate mặc định; search `code`, `name`; filter `category`
- [ ] `catalog/filters.py`:
    - `MaterialFilter` — filter `category`; search `code`, `name`

## URLs

- [x] `catalog/urls.py`:
    - `DefaultRouter` register: `materials`, `categories`, `units`
    - Route phẳng cho PUT/DELETE UnitConversion: `path('api/unit-conversions/<id>/', ...)`
- [x] Include vào `config/urls.py`: `path("api/", include("catalog.urls"))`

## Permissions

- [x] Material: Write → `IsAdminOrStorekeeper`; Read → `IsAuthenticated`
- [x] Category, Unit, Conversion: Write → `IsAdminOrStorekeeper`; Read → `IsAuthenticated`

## Tests

- [x] `catalog/tests.py`: 39 tests
    - MaterialCategory: 15 tests (tree mode, flat mode, depth, color, CRUD, permissions, hard-delete)
    - Material: 10 tests (GET list/detail auth+unauth, POST admin+storekeeper+unauth, PUT, DELETE)
    - Unit: 5 tests (CRUD + permissions)
    - UnitConversion: 9 tests (nested GET, POST material+global, PUT, DELETE)
- [x] Chạy `python manage.py test catalog` → 39/39 OK

## Seed Data

- [ ] `catalog/management/commands/seed_catalog.py`: data mẫu cho demo + test

### Danh mục (tree 2 cấp)

| code        | name              | parent | color  |
| ----------- | ----------------- | ------ | ------ |
| `VLXD`      | Vật liệu xây dựng | NULL   | blue   |
| `XM`        | Xi măng           | VLXD   | red    |
| `THEP`      | Thép              | VLXD   | green  |
| `THEP_TRON` | Thép tròn         | THEP   | orange |
| `CAT`       | Cát               | VLXD   | null   |
| `DA`        | Đá                | VLXD   | null   |
| `GACH`      | Gạch              | VLXD   | null   |

### Đơn vị

| code   | name     |
| ------ | -------- |
| `BAO`  | Bao      |
| `KG`   | Kilogram |
| `TAN`  | Tấn      |
| `M3`   | Mét khối |
| `CAY`  | Cây      |
| `VIEN` | Viên     |

### Vật tư (10 mẫu)

| code          | name                  | category  | unit |
| ------------- | --------------------- | --------- | ---- |
| `XM-HT-PCB40` | Xi măng Hà Tiên PCB40 | XM        | BAO  |
| `XM-BS-PCB30` | Xi măng Bỉm Sơn PCB30 | XM        | BAO  |
| `THEP-D10`    | Thép D10              | THEP_TRON | KG   |
| `THEP-D12`    | Thép D12              | THEP_TRON | KG   |
| `CAT-VANG`    | Cát vàng              | CAT       | M3   |
| `CAT-DEN`     | Cát đen               | CAT       | M3   |
| `DA-1X2`      | Đá 1x2                | DA        | M3   |
| `DA-4X6`      | Đá 4x6                | DA        | M3   |
| `GACH-ONG`    | Gạch ống 4 lỗ         | GACH      | VIEN |
| `GACH-THEP`   | Gạch thẻ              | GACH      | VIEN |

### Quy đổi (5 mẫu)

| from | to  | factor | material    | scope    |
| ---- | --- | ------ | ----------- | -------- |
| TAN  | KG  | 1000   | NULL        | global   |
| M3   | KG  | 1600   | CAT-VANG    | material |
| BAO  | KG  | 50     | XM-HT-PCB40 | material |
| BAO  | KG  | 40     | XM-BS-PCB30 | material |
| CAY  | KG  | 7.4    | THEP-D10    | material |

- [ ] Chạy `python manage.py seed_catalog`

## Tài liệu

- [ ] Cập nhật `docs/entities/README.md` — trạng thái Material: ✅ Done
- [ ] Cập nhật `docs/entities/material/change-log.md` — v1.0 checklist done
