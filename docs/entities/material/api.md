# API Endpoints — Catalog (Material + Category + Unit)

## Tổng quan

| Resource         | Prefix                         | ViewSet                    | Pagination             |
| ---------------- | ------------------------------ | -------------------------- | ---------------------- |
| Material         | `/api/materials/`              | `MaterialViewSet`          | Có (mặc định)          |
| MaterialCategory | `/api/categories/`             | `MaterialCategoryViewSet`  | **Không** (≤ 30 items) |
| Unit             | `/api/units/`                  | `UnitViewSet`              | **Không** (≤ 20 items) |
| UnitConversion   | `/api/units/{id}/conversions/` | `@action` trên UnitViewSet | **Không**              |

> **Tại sao UnitConversion nằm dưới Unit?** Quy đổi luôn bắt đầu từ 1 đơn vị gốc (vd: "1 bao = ? kg"). Đặt dưới Unit giúp UI tự nhiên: vào trang chi tiết `BAO` → thấy tất cả quy đổi từ `BAO` sang các đơn vị khác.

---

## 1. Material — `/api/materials/`

### Endpoints

| Method   | Endpoint               | Mô tả                        | Permission               |
| -------- | ---------------------- | ---------------------------- | ------------------------ |
| `GET`    | `/api/materials/`      | Danh sách vật tư (paginated) | IsAuthenticated          |
| `POST`   | `/api/materials/`      | Tạo vật tư mới               | **IsAdminOrStorekeeper** |
| `GET`    | `/api/materials/{id}/` | Chi tiết vật tư              | IsAuthenticated          |
| `PUT`    | `/api/materials/{id}/` | Cập nhật vật tư              | **IsAdminOrStorekeeper** |
| `DELETE` | `/api/materials/{id}/` | Vô hiệu hóa (soft delete)    | **IsAdminOrStorekeeper** |

**Query params:**

- `?category=1` — filter theo danh mục
- `?isActive=true` — filter trạng thái
- `?search=xi măng` — tìm theo `code` hoặc `name`

### Request/Response mẫu

**`GET /api/materials/`**

```json
{
    "items": [
        {
            "id": 1,
            "code": "XM-HT-PCB40",
            "name": "Xi măng Hà Tiên PCB40",
            "category": { "id": 2, "code": "XM", "name": "Xi măng" },
            "unit": { "id": 1, "code": "BAO", "name": "Bao" },
            "description": "PCB40, 50kg/bao",
            "isActive": true,
            "createdAt": "2026-08-05T00:00:00Z",
            "updatedAt": "2026-08-05T00:00:00Z"
        }
    ],
    "meta": {
        "page": 1,
        "pageSize": 20,
        "total": 150,
        "totalPages": 8,
        "hasNextPage": true,
        "hasPreviousPage": false
    }
}
```

**`POST /api/materials/`**

```json
// Request — Admin hoặc Thủ kho
{
    "code": "XM-HT-PCB40",
    "name": "Xi măng Hà Tiên PCB40",
    "categoryId": 2,
    "unitId": 1,
    "description": "PCB40, 50kg/bao"
}

// Response: 201 Created
```

**`GET /api/materials/1/`**

```json
{
    "id": 1,
    "code": "XM-HT-PCB40",
    "name": "Xi măng Hà Tiên PCB40",
    "category": { "id": 2, "code": "XM", "name": "Xi măng" },
    "unit": { "id": 1, "code": "BAO", "name": "Bao" },
    "description": "PCB40, 50kg/bao",
    "isActive": true,
    "createdAt": "2026-08-05T00:00:00Z",
    "updatedAt": "2026-08-05T00:00:00Z"
}
```

---

## 2. MaterialCategory — `/api/categories/`

| Method   | Endpoint                | Mô tả                               | Permission               |
| -------- | ----------------------- | ----------------------------------- | ------------------------ |
| `GET`    | `/api/categories/`      | Danh sách danh mục (không paginate) | IsAuthenticated          |
| `POST`   | `/api/categories/`      | Tạo danh mục mới                    | **IsAdminOrStorekeeper** |
| `GET`    | `/api/categories/{id}/` | Chi tiết danh mục                   | IsAuthenticated          |
| `PUT`    | `/api/categories/{id}/` | Cập nhật                            | **IsAdminOrStorekeeper** |
| `DELETE` | `/api/categories/{id}/` | Vô hiệu hóa                         | **IsAdminOrStorekeeper** |

**Query params:**

- `?flat=true` — trả danh sách phẳng kèm `depth` (dùng cho select box, không có `children`). Mặc định (`?flat=false` hoặc không có param) trả cây lồng.

### Mặc định — Dạng cây lồng toàn bộ

**`GET /api/categories/`** (chỉ trả node gốc, `children` lồng đệ quy toàn bộ cây)

```json
[
    {
        "id": 1,
        "code": "VLXD",
        "name": "Vật liệu xây dựng",
        "color": "blue",
        "parent": null,
        "children": [
            {
                "id": 2,
                "code": "XM",
                "name": "Xi măng",
                "color": "red",
                "parent": 1,
                "children": []
            },
            {
                "id": 4,
                "code": "THEP",
                "name": "Thép",
                "color": "green",
                "parent": 1,
                "children": [
                    {
                        "id": 5,
                        "code": "THEP_TRON",
                        "name": "Thép tròn",
                        "color": "orange",
                        "parent": 4,
                        "children": []
                    }
                ]
            },
            {
                "id": 6,
                "code": "CAT",
                "name": "Cát",
                "color": null,
                "parent": 1,
                "children": []
            }
        ],
        "isActive": true
    }
]
```

### Dạng phẳng (cho select box)

**`GET /api/categories/?flat=true`** (danh sách phẳng, pre-order, kèm `depth`)

```json
[
    {
        "id": 1,
        "code": "VLXD",
        "name": "Vật liệu xây dựng",
        "color": "blue",
        "parent": null,
        "depth": 0,
        "isActive": true
    },
    {
        "id": 2,
        "code": "XM",
        "name": "Xi măng",
        "color": "red",
        "parent": 1,
        "depth": 1,
        "isActive": true
    },
    {
        "id": 4,
        "code": "THEP",
        "name": "Thép",
        "color": "green",
        "parent": 1,
        "depth": 1,
        "isActive": true
    },
    {
        "id": 5,
        "code": "THEP_TRON",
        "name": "Thép tròn",
        "color": "orange",
        "parent": 4,
        "depth": 2,
        "isActive": true
    },
    {
        "id": 6,
        "code": "CAT",
        "name": "Cát",
        "color": null,
        "parent": 1,
        "depth": 1,
        "isActive": true
    }
]
```

> **`depth`** là độ sâu trong cây, tính từ gốc (0). Duyệt theo thứ tự **pre-order** (cha → con → cháu). Frontend dùng `depth` để thêm padding-left khi render select box, tạo hiệu ứng phân cấp trực quan mà không cần TreeSelect component.

---

## 3. Unit — `/api/units/`

| Method   | Endpoint           | Mô tả                             | Permission               |
| -------- | ------------------ | --------------------------------- | ------------------------ |
| `GET`    | `/api/units/`      | Danh sách đơn vị (không paginate) | IsAuthenticated          |
| `POST`   | `/api/units/`      | Tạo đơn vị                        | **IsAdminOrStorekeeper** |
| `GET`    | `/api/units/{id}/` | Chi tiết đơn vị                   | IsAuthenticated          |
| `PUT`    | `/api/units/{id}/` | Cập nhật                          | **IsAdminOrStorekeeper** |
| `DELETE` | `/api/units/{id}/` | Vô hiệu hóa                       | **IsAdminOrStorekeeper** |

**`GET /api/units/`**

```json
[
    { "id": 1, "code": "BAO", "name": "Bao", "isActive": true },
    { "id": 2, "code": "KG", "name": "Kilogram", "isActive": true },
    { "id": 3, "code": "TAN", "name": "Tấn", "isActive": true },
    { "id": 4, "code": "M3", "name": "Mét khối", "isActive": true }
]
```

---

## 4. UnitConversion — `/api/units/{id}/conversions/`

Quy đổi được đặt dưới Unit thông qua `@action` trên `UnitViewSet`.

| Method   | Endpoint                       | Mô tả                             |
| -------- | ------------------------------ | --------------------------------- |
| `GET`    | `/api/units/{id}/conversions/` | Danh sách quy đổi của unit này    |
| `POST`   | `/api/units/{id}/conversions/` | Tạo quy đổi mới cho unit này      | **IsAdminOrStorekeeper** |
| `PUT`    | `/api/unit-conversions/{id}/`  | Cập nhật quy đổi — endpoint phẳng | **IsAdminOrStorekeeper** |
| `DELETE` | `/api/unit-conversions/{id}/`  | Xóa quy đổi — endpoint phẳng      | **IsAdminOrStorekeeper** |

> **Tại sao PUT/DELETE dùng endpoint phẳng?** GET list + POST create được gom dưới Unit vì `from_unit` đã biết từ URL. PUT/DELETE thao tác trên 1 conversion cụ thể, không cần biết `from_unit` → dùng endpoint phẳng `/api/unit-conversions/{id}/` cho gọn.

**`GET /api/units/1/conversions/`** (Unit id=1 là "BAO")

```json
{
    "unit": { "id": 1, "code": "BAO", "name": "Bao" },
    "conversions": [
        {
            "id": 2,
            "toUnit": { "id": 2, "code": "KG", "name": "Kilogram" },
            "factor": "50.0000",
            "material": {
                "id": 1,
                "code": "XM-HT-PCB40",
                "name": "Xi măng Hà Tiên PCB40"
            },
            "scope": "material"
        },
        {
            "id": 3,
            "toUnit": { "id": 2, "code": "KG", "name": "Kilogram" },
            "factor": "40.0000",
            "material": {
                "id": 2,
                "code": "XM-BS-PCB30",
                "name": "Xi măng Bỉm Sơn PCB30"
            },
            "scope": "material"
        }
    ],
    "globalConversions": []
}
```

**`POST /api/units/1/conversions/`** (tạo quy đổi từ BAO)

```json
// Request — quy đổi riêng cho vật tư
{
  "toUnitId": 2,
  "factor": 50,
  "materialId": 1
}

// Request — quy đổi toàn cục
{
  "toUnitId": 2,
  "factor": 1000
}

// Response: 201 Created — trả về object conversion vừa tạo
```

**`PUT /api/unit-conversions/2/`**

```json
// Request
{
    "factor": 55
}
```

**`DELETE /api/unit-conversions/2/`** → `204 No Content`

---

## 5. UI hiển thị UnitConversion — giải thích

Khi người dùng xem trang chi tiết của Unit `BAO`:

```
┌─────────────────────────────────────────────┐
│  BAO (Bao)                                  │
│                                             │
│  Quy đổi riêng (theo vật tư):               │
│  ┌──────────────────────────────────────┐   │
│  │ 1 BAO = 50.0 KG  │ Xi măng Hà Tiên  │   │
│  │ 1 BAO = 40.0 KG  │ Xi măng Bỉm Sơn  │   │
│  └──────────────────────────────────────┘   │
│                                             │
│  Quy đổi toàn cục:                          │
│  ┌──────────────────────────────────────┐   │
│  │ (trống — BAO không có quy đổi chung) │   │
│  └──────────────────────────────────────┘   │
│                                             │
│  [+ Thêm quy đổi]                           │
└─────────────────────────────────────────────┘
```

Còn với Unit `TAN`:

```
┌─────────────────────────────────────────────┐
│  TAN (Tấn)                                  │
│                                             │
│  Quy đổi toàn cục:                          │
│  ┌──────────────────────────────────────┐   │
│  │ 1 TAN = 1000.0 KG                    │   │
│  └──────────────────────────────────────┘   │
│                                             │
│  Quy đổi riêng (theo vật tư):               │
│  ┌──────────────────────────────────────┐   │
│  │ (trống)                              │   │
│  └──────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

**Đây KHÔNG phải là "tạo 1 Unit tên là bao xi măng".** Unit `BAO` vẫn là đơn vị chung "bao". `UnitConversion` chỉ trả lời câu hỏi: **"1 bao của vật tư X nặng bao nhiêu kg?"** — không tạo ra đơn vị mới.
