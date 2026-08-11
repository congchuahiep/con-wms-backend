# Model — Unit + UnitConversion

> Django app: `catalog`
> Kế thừa: `models.Model`

## 1. Unit

### 1.1 Fields hiện tại (giữ nguyên)

| # | Field | Kiểu | Ràng buộc | Ghi chú |
|---|---|---|---|---|
| 1 | `id` | BigAutoField (PK) | | |
| 2 | `code` | CharField(10) | unique | Mã đơn vị (BAO, KG, TAN...) |
| 3 | `name` | CharField(100) | | Tên hiển thị |
| 4 | `is_active` | BooleanField | default=True | Soft delete |
| 5 | `created_at` | DateTimeField | auto_now_add | |
| 6 | `updated_at` | DateTimeField | auto_now | |

### 1.2 Field mới — `conversion_type`

| # | Field | Kiểu | Ràng buộc | Ghi chú |
|---|---|---|---|---|
| 7 | `conversion_type` | CharField(10) | choices, default="global" | `"global"` hoặc `"material"` |

```python
class UnitConversionType(models.TextChoices):
    GLOBAL = "global", "Quy đổi toàn cục"
    MATERIAL = "material", "Quy đổi theo vật tư"
```

**Ràng buộc nghiệp vụ (enforced ở serializer, không phải DB constraint):**

| `conversion_type` | `UnitConversion.material` | Mô tả |
|---|---|---|
| `global` | **Phải là NULL** | Từ chối nếu có material |
| `material` | **Bắt buộc có** | Từ chối nếu thiếu material |

## 2. UnitConversion

### 2.1 Fields (giữ nguyên, không thay đổi)

| # | Field | Kiểu | Ràng buộc | Ghi chú |
|---|---|---|---|---|
| 1 | `id` | BigAutoField (PK) | | |
| 2 | `from_unit` | FK → Unit | PROTECT | Đơn vị gốc |
| 3 | `to_unit` | FK → Unit | PROTECT | Đơn vị đích |
| 4 | `factor` | DecimalField(12,4) | | Hệ số quy đổi (luôn > 0) |
| 5 | `material` | FK → Material | CASCADE, nullable | NULL = global, có set = material-specific |
| 6 | `is_active` | BooleanField | default=True | Soft delete |
| 7 | `created_at` | DateTimeField | auto_now_add | |
| 8 | `updated_at` | DateTimeField | auto_now | |

### 2.2 Unique constraint (giữ nguyên)

```python
models.UniqueConstraint(
    fields=["from_unit", "to_unit", "material"],
    name="uq_unit_conversion",
)
```

## 3. Reverse Virtual — logic

Không lưu DB row cho chiều ngược. Khi query `GET /api/units/{id}/`:

```
Query 1: UnitConversion.objects.filter(from_unit=obj, is_active=True)   ← direct
Query 2: UnitConversion.objects.filter(to_unit=obj, is_active=True, material__isnull=True) ← reverse (chỉ global)
```

Với mỗi row reverse:
- `to_unit` trong response = `from_unit` của row gốc (đơn vị đích bị đảo)
- `factor` trong response = `1 ÷ factor_gốc`
- `is_reverse` = `true`

**Material-specific KHÔNG reverse.** `1 BAO gạo = 50 KG` chỉ có ý nghĩa khi đứng ở BAO. KG là global, không thể reverse ra BAO.

## 4. Enums

| Enum | Values | Dùng ở |
|---|---|---|
| `UnitConversionType` | `GLOBAL`, `MATERIAL` | `Unit.conversion_type` |

## 5. Quan hệ

```
Unit ──┬── conversion_type (global | material)
       │
       ├── conversions_from (1→N UnitConversion, FK: from_unit)
       │
       └── conversions_to   (1→N UnitConversion, FK: to_unit) ← dùng cho reverse lookup

UnitConversion ──FK──▶ Material (nullable)
```

## 6. Quyết định thiết kế

| # | Quyết định | Lý do |
|---|---|---|
| **D1** | `conversion_type` trên `Unit` thay vì để `UnitConversion.material` nullable tự do | Tránh trộn lẫn global/material trên cùng 1 unit. Mỗi unit chỉ thuộc 1 loại: hoặc quy đổi không phụ thuộc vật tư (KG, TAN, M3), hoặc quy đổi luôn gắn với vật tư (BAO, CAY, VIEN). |
| **D2** | Ràng buộc ở tầng serializer, không phải DB constraint | Django không hỗ trợ conditional FK constraint. Serializer `validate()` đủ mạnh cho mục đích này. |
| **D3** | Reverse lookup virtual, không lưu DB | Tránh trùng lặp dữ liệu. Khi update `1 TAN = 1000 KG` → `1 TAN = 1200 KG`, chỉ cần update 1 row, không cần sync row ngược. |
| **D4** | Reverse chỉ áp dụng cho global | `1 KG = 0.02 BAO gạo` là vô nghĩa. Material-specific chỉ có chiều xuôi từ đơn vị đặc thù (BAO) sang đơn vị chuẩn (KG). |
| **D5** | Reverse trả `id` thật của row gốc, kèm `isReverse: true` | FE có `id` để PUT/PATCH. Khi edit factor, FE tự tính `1 ÷ factor_mới` rồi gửi PUT với factor xuôi lên server. |
| **D6** | Merge `globalConversions` + `materialConversions` → 1 list `conversions` | Với `conversion_type` trên Unit, response chỉ chứa 1 loại duy nhất. Tách làm 2 list là dư thừa. |
| **D7** | `material` luôn có trong response, giá trị `null` với global | Đồng nhất shape giữa 2 loại conversion. FE chỉ cần parse 1 kiểu dữ liệu. |
| **D8** | `UniqueConstraint` partial (có `condition`) | `(from_unit, to_unit)` unique khi `material IS NULL`; `(from_unit, to_unit, material)` unique khi `material IS NOT NULL`. SQL không coi `NULL = NULL` nên constraint cũ bị vô hiệu với global. |
| **D9** | Cấm reverse pair (`TAN→KG` → từ chối `KG→TAN`) | API đã có reverse virtual, tạo chiều ngược gây trùng lặp dữ liệu. Validate ở serializer, không phải DB constraint. |
| **D10** | Validate uniqueness trong `validate()` (không chỉ DB constraint) | Trả 400 + message rõ ràng cho client thay vì IntegrityError 500. DB constraint vẫn giữ làm safety net. |
| **D11** | `DELETE /api/unit-conversions/{id}/` → hard delete + 200 + object | UnitConversion là mapping đơn giản, không cần soft delete. Trả về object để client cập nhật local state. |
