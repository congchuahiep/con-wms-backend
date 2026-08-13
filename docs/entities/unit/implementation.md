# Implementation Checklist — Unit + UnitConversion (v1.3)

## Model

- [x] Thêm `UnitConversionType` TextChoices vào `catalog/models.py`
- [x] Thêm `conversion_type` field vào `Unit` model
- [x] Chạy `python manage.py makemigrations catalog` + `migrate` (0003)
- [x] Sửa UniqueConstraint: 2 partial thay vì 1 (0004)
    - [x] `uq_unit_conversion_global`: `(from_unit, to_unit)` khi `material IS NULL`
    - [x] `uq_unit_conversion_material`: `(from_unit, to_unit, material)` khi `material IS NOT NULL`
- [ ] Data migration: đặt `conversion_type` cho các unit hiện có

## Serializer

- [x] `UnitSerializer`: thêm `conversion_type` vào `fields`
- [x] `UnitConversionSerializer`:
    - [x] Thêm `is_reverse = BooleanField(read_only=True, default=False)`
    - [x] Override `to_representation()`: reverse context → đảo + `_format_factor()`
    - [x] Override `validate()`: 3 lớp kiểm tra
        - [x] `conversion_type` constraint (global/material phải khớp với có/không material)
        - [x] Cấm reverse pair cho global (đã có `A→B` thì từ chối `B→A`)
        - [x] Uniqueness check (thay cho IntegrityError 500)
    - [x] `_format_factor()`: strip trailing zeros (`"500.0000"` → `"500"`)
    - [x] Xóa field `scope`
- [x] `DetailedUnitSerializer`:
    - [x] Đổi `conversions` + `global_conversions` → 1 field `conversions`
    - [x] Thêm `conversion_type` vào fields
    - [x] `get_conversions()`: query direct + reverse (chỉ global)
    - [x] `@extend_schema_field(UnitConversionSerializer(many=True))`
    - [x] Xóa inner serializer classes (đã lỗi thời)

## Views

- [x] `UnitViewSet`:
    - [x] `retrieve` → `DetailedUnitSerializer` (gộp luôn conversions)
    - [x] Xóa `list_conversions` GET action
    - [x] `create_conversion` → standalone `@action(detail=True, methods=["post"], url_path="conversions")`
    - [x] Truyền `from_unit` vào serializer context
- [x] `UnitConversionViewSet`:
    - [x] `destroy` → hard delete + trả về 200 + object vừa xóa
    - [x] Permission: `IsAdminOrStorekeeper`
- [x] Cập nhật extend_schema description/tags

## Tests

- [x] Cập nhật response shape (flat, single `conversions`, detail URL)
- [x] `conversion_type` validation:
    - [x] Global có materialId → 400
    - [x] Material thiếu materialId → 400
- [x] Reverse:
    - [x] GET KG thấy reverse từ TAN với `isReverse: true`
    - [x] GET BAO KHÔNG có reverse (material-specific)
    - [x] Cấm POST reverse pair cho global → 400
- [x] Uniqueness: TAN→KG đã có, POST lại TAN→KG → 400
- [x] Hard delete: DELETE → 200 + object, row bị xóa khỏi DB
- [x] Chạy `python manage.py test catalog` → **39/39 OK**
- [x] Schema valid: `python manage.py spectacular --validate`

## Seed Data

- [ ] Cập nhật `seed_catalog.py`: thêm `conversion_type` cho mỗi unit
- [ ] Chạy `python manage.py seed_catalog`

## Data Migration Guide

| Unit | conversion_type | Lý do |
|------|:---:|---|
| `BAO` | `material` | Mỗi loại vật tư 1 trọng lượng bao khác nhau |
| `CAY` | `material` | Mỗi loại thép 1 trọng lượng/cây khác nhau |
| `VIEN` | `material` | Mỗi loại gạch 1 kích thước/trọng lượng khác nhau |
| `KG` | `global` | 1 KG luôn = 1 KG, không phụ thuộc vật tư |
| `TAN` | `global` | 1 Tấn luôn = 1000 KG |
| `M3` | `global` | 1 Mét khối luôn = 1000 Lít |

## Tài liệu

- [x] Cập nhật `docs/entities/README.md` — thêm entity `Unit`
- [x] Cập nhật `docs/entities/material/README.md` — ghi chú Unit + UnitConversion đã tách riêng
- [x] `docs/entities/unit/change-log.md` — v1.3 release notes
- [x] `docs/entities/unit/frontend-migration.md` — FE migration guide
