# Frontend Spec — Trang Material

## API endpoints

| Method   | URL                                      | Dùng cho                    |
| -------- | ---------------------------------------- | --------------------------- |
| `GET`    | `/api/materials/?search=...&category=id` | Danh sách (có phân trang)   |
| `POST`   | `/api/materials/`                        | Tạo mới                     |
| `PUT`    | `/api/materials/{id}/`                   | Sửa                         |
| `DELETE` | `/api/materials/{id}/`                   | Soft delete                 |
| `GET`    | `/api/categories/?flat=true`             | Select box chọn Danh mục    |
| `GET`    | `/api/units/`                            | Select box chọn Đơn vị tính |

## Response shape

### GET list (paginated)

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
            "createdAt": "...",
            "updatedAt": "..."
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

### POST/PUT request body

```json
{
    "code": "XM-HT-PCB40",
    "name": "Xi măng Hà Tiên PCB40",
    "categoryId": 2,
    "unitId": 1,
    "description": "PCB40, 50kg/bao"
}
```

## UI cần làm

### 1. Danh sách Material (table + pagination)

- Cột: Mã, Tên, Danh mục (tên + màu), Đơn vị, Mô tả, Trạng thái
- Search bar (tìm theo mã/tên)
- Filter dropdown theo Category
- Nút "Thêm vật tư"

### 2. Form tạo / sửa Material

- `code` — text input (bắt buộc, max 30 ký tự)
- `name` — text input (bắt buộc)
- `categoryId` — select box (load từ `GET /api/categories/?flat=true`, hiển thị indent theo `depth`)
- `unitId` — select box (load từ `GET /api/units/`)
- `description` — textarea (optional)

### 3. Soft delete

- Confirm dialog → `DELETE`
- Row ẩn khỏi list (vì API chỉ trả `isActive=true`)

## Lưu ý

- Category select box nên dùng API `?flat=true` để có field `depth` → indent tên danh mục theo cấp (VLXD, → Xi măng, → Thép...)
- Unit select box hiển thị `code - name` (vd: "BAO - Bao"). Có thể nhóm theo `conversionType` nếu muốn đẹp hơn nhưng không bắt buộc.
- Form tạo/sửa: validate `code` không trùng (server trả 400, hiển thị lỗi dưới field)
