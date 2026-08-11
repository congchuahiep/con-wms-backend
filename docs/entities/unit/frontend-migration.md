# Frontend Migration Guide — Unit + UnitConversion v1.3

> **TL;DR**: `GET /api/units/{id}/` giờ đã trả về kèm `conversions`. Endpoint `GET /api/units/{id}/conversions/` đã bị xóa. Có thêm `conversionType`, `isReverse`. Có reverse virtual. Cách edit reverse entry đặc biệt.

---

## 1. Breaking Changes Summary

| Thay đổi                                            | Cũ                                                                      | Mới                                                                           |
| --------------------------------------------------- | ----------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| Endpoint GET list conversions                       | `GET /api/units/{id}/conversions/`                                      | **Xóa** — dùng `GET /api/units/{id}/` ([Unit detail](#3-get-apiunitsid--response-mới)) |
| Response shape `GET /api/units/{id}/`               | Chỉ có field cơ bản (`id, code, name, ...`)                             | Thêm `conversionType`, `conversions: [...]`                                   |
| Tách global/material                                | 2 key riêng                                                             | 1 key `conversions`, loại nào do `conversionType` quyết định                  |
| `Unit` có field mới                                 | Không                                                                   | `conversionType`: `"global"` hoặc `"material"`                                |
| Conversion có field `scope`                         | Có (`"global"` / `"material"`)                                          | **Bỏ**                                                                        |
| Conversion có field `isReverse`                     | Không                                                                   | Có (`true` / `false`)                                                         |
| Reverse lookup                                      | Không có                                                                | Có (với global unit). Xem mục 4.                                              |
| `PUT /api/unit-conversions/{id}/`                   | Có thể gửi `materialId` để đổi material                                 | Chỉ gửi field cần update (thường là `factor`). Material cố định.              |
| Permission                                          | Admin hoặc Thủ kho                                                      | Admin hoặc Thủ kho (giữ nguyên)                                               |
| `DELETE /api/unit-conversions/{id}/`                | `204 No Content` (soft delete)                                           | `200 OK` + object vừa xóa (hard delete)                                       |
| `factor` format                                     | `"500.0000"` (đủ 4 chữ số thập phân)                                   | `"500"` (strip trailing zeros)                                              |

---

## 2. `Unit` — field mới `conversionType`

### TypeScript type

```ts
type UnitConversionType = "global" | "material";

interface Unit {
    id: number;
    code: string;
    name: string;
    conversionType: UnitConversionType; // ← NEW
    isActive: boolean;
    createdAt: string;
    updatedAt: string;
}
```

### Cách dùng

- Khi tạo Unit: luôn chọn `conversionType`.
- Khi tạo Conversion cho Unit: UI tự động hiển thị/ẩn trường chọn Material dựa trên `conversionType`.
    - `global` → ẩn Material selector
    - `material` → hiện Material selector, bắt buộc chọn

---

## 3. `GET /api/units/{id}/` — Response mới

### TypeScript type

```ts
interface UnitConversion {
    id: number; // id thật trong DB (dùng để PUT/DELETE)
    toUnit: {
        id: number;
        code: string;
        name: string;
    };
    factor: string; // decimal string, ví dụ "1000.0000"
    material: {
        // null nếu global
        id: number;
        code: string;
        name: string;
    } | null;
    isReverse: boolean; // ← NEW: true nếu đây là chiều ngược (virtual)
}

interface UnitDetailResponse {
    id: number;
    code: string;
    name: string;
    conversionType: UnitConversionType;
    isActive: boolean;
    createdAt: string;
    updatedAt: string;
    conversions: UnitConversion[];
}
```

### Migration code (pseudo)

```ts
// Cũ
const { unit, globalConversions, materialConversions } = response;
const allConversions = [...globalConversions, ...materialConversions];

// Mới
const { conversions, ...unitFields } = response;
// unitFields đã bao gồm conversionType
// conversions đã gộp sẵn direct + reverse
```

---

## 4. Reverse Virtual — cách handle

### Nhận diện

Entry có `isReverse: true` là reverse virtual. Ví dụ khi xem `KG`:

```json
{
    "id": 3, // ← id thật của row "1 TAN = 1000 KG"
    "toUnit": { "id": 3, "code": "TAN", "name": "Tấn" },
    "factor": "0.0010", // ← đã đảo 1/1000
    "material": null,
    "isReverse": true
}
```

### Hiển thị

Bình thường như mọi entry khác. Chỉ cần gắn tag "Reverse" hoặc icon nhỏ để user biết.

### Chỉnh sửa factor

User sửa `0.001` → `0.002` (tức `1 KG = 0.002 TAN`):

```ts
// 1. FE tính factor xuôi
const reverseFactor = 0.002;
const forwardFactor = 1 / reverseFactor; // = 500

// 2. Gửi PUT với factor xuôi
PUT /api/unit-conversions/3/
Body: { "factor": 500 }

// → Row gốc "1 TAN = 500 KG" được update
// → Lần GET sau sẽ thấy reverse: "1 KG = 0.002 TAN"
```

**Quan trọng**: Luôn gửi `id` thật và `factor` xuôi. Server không biết FE đang hiển thị ở chiều nào.

### Xóa

```
DELETE /api/unit-conversions/3/
→ 200 OK + object vừa xóa (có thể dùng để remove khỏi local state)
→ Row bị xóa cứng khỏi DB. Reverse cũng biến mất.
```

---

## 5. Tạo Conversion — validation mới

### Global unit (conversionType = "global")

```ts
// ✅ Hợp lệ
POST /api/units/3/conversions/
Body: { "toUnitId": 2, "factor": 1000 }

// ❌ Server trả 400 nếu gửi kèm materialId
Body: { "toUnitId": 2, "factor": 1000, "materialId": 1 }
// → { "materialId": ["Đơn vị toàn cục không được gán vật tư."] }
```

### Material unit (conversionType = "material")

```ts
// ✅ Hợp lệ
POST /api/units/1/conversions/
Body: { "toUnitId": 2, "factor": 50, "materialId": 1 }

// ❌ Server trả 400 nếu thiếu materialId
Body: { "toUnitId": 2, "factor": 50 }
// → { "materialId": ["Đơn vị theo vật tư bắt buộc phải chọn vật tư."] }
```

### UI recommendation

Khi mở form "Thêm quy đổi" cho 1 Unit:

```ts
if (unit.conversionType === "global") {
    // Ẩn dropdown chọn Material
    // Chỉ hiện: chọn toUnit + nhập factor
} else {
    // Hiện dropdown chọn Material (bắt buộc)
    // Hiện: chọn Material + chọn toUnit + nhập factor
}
```

---

## 6. Bỏ field `scope`

Trước đây mỗi conversion có field `scope: "global" | "material"`. Từ v1.3 field này **bị xóa**. Thay vào đó, dùng `unit.conversionType` để biết loại.

```ts
// Cũ
const scope = conversion.scope;

// Mới
const scope = unit.conversionType; // "global" hoặc "material"
```

---

## 7. URL changes

| Method   | Cũ                             | Mới                                            |
| -------- | ------------------------------ | ---------------------------------------------- |
| `GET`    | `/api/units/{id}/conversions/` | `/api/units/{id}/` (detail, đã có `conversions`) |
| `POST`   | `/api/units/{id}/conversions/` | `/api/units/{id}/conversions/` (không đổi)      |
| `PUT`    | `/api/unit-conversions/{id}/`  | `/api/unit-conversions/{id}/` (không đổi)       |
| `DELETE` | `/api/unit-conversions/{id}/`  | `/api/unit-conversions/{id}/` (không đổi)       |
