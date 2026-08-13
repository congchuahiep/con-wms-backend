# API Endpoints — Unit + UnitConversion

## Tổng quan

| Resource       | Prefix                         | ViewSet                    | Pagination             |
| -------------- | ------------------------------ | -------------------------- | ---------------------- |
| Unit           | `/api/units/`                  | `UnitViewSet`              | **Không** (≤ 20 items) |
| UnitConversion | `/api/units/{id}/conversions/` | `@action` trên UnitViewSet | **Không**              |
| UnitConversion | `/api/unit-conversions/{id}/`  | `UnitConversionViewSet`    | — (chỉ PUT/DELETE)     |

> **Tại sao UnitConversion GET list không có endpoint riêng?** `GET /api/units/{id}/` đã trả về `DetailedUnitSerializer` kèm danh sách `conversations` (cả direct + reverse). Không cần thêm endpoint `/conversions/` cho GET.

---

## 1. Unit — `/api/units/`

| Method   | Endpoint           | Mô tả                             | Permission      |
| -------- | ------------------ | --------------------------------- | --------------- |
| `GET`    | `/api/units/`      | Danh sách đơn vị (không paginate) | IsAuthenticated |
| `POST`   | `/api/units/`      | Tạo đơn vị mới                    | IsAdmin         |
| `GET`    | `/api/units/{id}/` | Chi tiết đơn vị                   | IsAuthenticated |
| `PUT`    | `/api/units/{id}/` | Cập nhật đơn vị                   | IsAdmin         |
| `DELETE` | `/api/units/{id}/` | Xóa đơn vị (hard delete)          | IsAdmin         |

### `GET /api/units/`

```json
[
    {
        "id": 1,
        "code": "BAO",
        "name": "Bao",
        "conversionType": "material",
        "createdAt": "2026-08-01T00:00:00Z",
        "updatedAt": "2026-08-01T00:00:00Z"
    },
    {
        "id": 2,
        "code": "KG",
        "name": "Kilogram",
        "conversionType": "global",
        "createdAt": "2026-08-01T00:00:00Z",
        "updatedAt": "2026-08-01T00:00:00Z"
    }
]
```

### `POST /api/units/`

```json
// Request
{
  "code": "BAO",
  "name": "Bao",
  "conversionType": "material"
}

// Response: 201 Created
{
  "id": 1,
  "code": "BAO",
  "name": "Bao",
  "conversionType": "material",
  "createdAt": "2026-08-01T00:00:00Z",
  "updatedAt": "2026-08-01T00:00:00Z"
}
```

---

## 2. UnitConversion

### GET — đã gộp vào `GET /api/units/{id}/`

Không có endpoint GET riêng cho list conversions. `GET /api/units/{id}/` trả về `DetailedUnitSerializer` đã bao gồm field `conversions`.

### POST `/api/units/{id}/conversions/`

| Method   | Endpoint                       | Mô tả                             | Permission           |
| -------- | ------------------------------ | --------------------------------- | -------------------- |
| `POST`   | `/api/units/{id}/conversions/` | Tạo quy đổi mới                   | IsAdminOrStorekeeper |
| `PUT`    | `/api/unit-conversions/{id}/`  | Cập nhật quy đổi (endpoint phẳng) | IsAdminOrStorekeeper |
| `DELETE` | `/api/unit-conversions/{id}/`  | Xóa quy đổi (hard delete)           | IsAdminOrStorekeeper |

### `GET /api/units/1/` — Unit "BAO" (material)

> BAO có `conversionType: "material"` → **chỉ có direct**, không reverse.

```json
{
    "id": 1,
    "code": "BAO",
    "name": "Bao",
    "conversionType": "material",
    "createdAt": "2026-08-01T00:00:00Z",
    "updatedAt": "2026-08-01T00:00:00Z",
    "conversions": [
        {
            "id": 1,
            "toUnit": { "id": 2, "code": "KG", "name": "Kilogram" },
            "factor": "50.0000",
            "material": {
                "id": 1,
                "code": "XM-HT-PCB40",
                "name": "Xi măng Hà Tiên PCB40"
            },
            "isReverse": false
        },
        {
            "id": 2,
            "toUnit": { "id": 2, "code": "KG", "name": "Kilogram" },
            "factor": "40.0000",
            "material": {
                "id": 2,
                "code": "XM-BS-PCB30",
                "name": "Xi măng Bỉm Sơn PCB30"
            },
            "isReverse": false
        }
    ]
}
```

### `GET /api/units/3/` — Unit "TAN" (global, có reverse)

> DB có 1 row: `1 TAN = 1000 KG`. Response gồm cả direct + reverse từ các global unit khác.

```json
{
    "id": 3,
    "code": "TAN",
    "name": "Tấn",
    "conversionType": "global",
    "createdAt": "2026-08-01T00:00:00Z",
    "updatedAt": "2026-08-01T00:00:00Z",
    "conversions": [
        {
            "id": 3,
            "toUnit": { "id": 2, "code": "KG", "name": "Kilogram" },
            "factor": "1000.0000",
            "material": null,
            "isReverse": false
        }
    ]
}
```

### `GET /api/units/2/` — Unit "KG" (global, reverse từ TAN)

> KG không có direct. Nhưng query reverse thấy row `1 TAN = 1000 KG` (to_unit=KG).
> → Trả về virtual: `1 KG = 0.0010 TAN`.

```json
{
    "id": 2,
    "code": "KG",
    "name": "Kilogram",
    "conversionType": "global",
    "createdAt": "2026-08-01T00:00:00Z",
    "updatedAt": "2026-08-01T00:00:00Z",
    "conversions": [
        {
            "id": 3,
            "toUnit": { "id": 3, "code": "TAN", "name": "Tấn" },
            "factor": "0.0010",
            "material": null,
            "isReverse": true
        }
    ]
}
```

> **`id: 3`**: chính là `id` của row gốc `1 TAN = 1000 KG`. FE dùng `id` này để PUT/PATCH.
> **`isReverse: true`**: FE biết factor này đã đảo. Khi edit, tự tính `1 ÷ factor_mới`.

### `POST /api/units/3/conversions/` — Tạo quy đổi cho Unit "TAN" (global)

```json
// Request — TAN là global, không được gửi materialId
{
  "toUnitId": 2,
  "factor": 1000
}

// Response: 201 Created
{
  "id": 4,
  "toUnit": { "id": 2, "code": "KG", "name": "Kilogram" },
  "factor": "1000.0000",
  "material": null,
  "isReverse": false
}
```

Nếu gửi kèm `materialId` khi `Unit.conversion_type == "global"`:

```json
// Response: 400 Bad Request
{
    "materialId": ["Đơn vị toàn cục không được gán vật tư."]
}
```

### `POST /api/units/1/conversions/` — Tạo quy đổi cho Unit "BAO" (material)

```json
// Request — BAO là material, BẮT BUỘC có materialId
{
  "toUnitId": 2,
  "factor": 50,
  "materialId": 1
}

// Response: 201 Created
{
  "id": 5,
  "toUnit": { "id": 2, "code": "KG", "name": "Kilogram" },
  "factor": "50.0000",
  "material": { "id": 1, "code": "XM-HT-PCB40", "name": "Xi măng Hà Tiên PCB40" },
  "isReverse": false
}
```

Nếu thiếu `materialId` khi `Unit.conversion_type == "material"`:

```json
// Response: 400 Bad Request
{
    "materialId": ["Đơn vị theo vật tư bắt buộc phải chọn vật tư."]
}
```

### `PUT /api/unit-conversions/{id}/`

Gửi `id` của row gốc (kể cả khi FE đang hiển thị ở dạng reverse):

```json
// Request — sửa factor của reverse entry 1 KG = 0.001 TAN → 1 KG = 0.00083 TAN
// FE tính: 1 ÷ 0.00083 ≈ 1200, gửi PUT với factor xuôi
{
  "factor": 1200
}

// Response: 200 OK
{
  "id": 3,
  "toUnit": { "id": 2, "code": "KG", "name": "Kilogram" },
  "factor": "1200.0000",
  "material": null,
  "isReverse": false
}
```

### `DELETE /api/unit-conversions/{id}/`

Xóa cứng (hard delete). Trả về `200 OK` + object vừa xóa:

```json
// Response: 200 OK
{
    "id": 3,
    "fromUnit": { "id": 3, "code": "TAN", "name": "Tấn" },
    "toUnit": { "id": 2, "code": "KG", "name": "Kilogram" },
    "factor": "1000",
    "material": null,
    "isReverse": false,
    "createdAt": "2026-08-09T00:00:00Z",
    "updatedAt": "2026-08-09T00:00:00Z"
}
```

---

## 3. So sánh với API cũ

|                                  | Cũ (v1.x)                                          | Mới (v1.3)                                     |
| -------------------------------- | -------------------------------------------------- | ---------------------------------------------- |
| Endpoint GET list conversions    | `GET /api/units/{id}/conversions/`                 | `GET /api/units/{id}/` (detail endpoint)       |
| Response shape                   | `{ unit, globalConversions, materialConversions }` | `{ ...unit flat fields, conversions }`         |
| Tách global/material             | 2 list riêng                                       | 1 list chung, `Unit.conversionType` quyết định |
| Reverse lookup                   | Không có                                           | Có (chỉ global), kèm `isReverse: true`         |
| `Unit` có field `conversionType` | Không                                              | Có                                             |
| Ràng buộc material               | Không (nullable tự do)                             | Có (validate theo `conversionType`)            |
| Cấm reverse pair                 | Không                                              | Có (`TAN→KG` → từ chối `KG→TAN`)               |
| Trùng lặp global                 | Cho phép (bug NULL)                                | Cấm (partial unique constraint)                |
| `scope` field                    | Có                                                 | **Bỏ**                                         |
| Trailing zeros trên factor       | `"500.0000"`                                       | `"500"`                                        |
| DELETE response                  | `204 No Content` (soft delete)                     | `200 OK` + object (hard delete)                |
