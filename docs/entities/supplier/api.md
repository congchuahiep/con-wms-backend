# API Endpoints — Supplier

## Danh sách endpoint

| Method   | Endpoint               | Mô tả                         | Request Body                                                                                                    | Response                           |
| -------- | ---------------------- | ----------------------------- | --------------------------------------------------------------------------------------------------------------- | ---------------------------------- |
| `GET`    | `/api/suppliers/`      | Danh sách nhà cung cấp        | —                                                                                                               | `{"count": N, "results": [{...}]}` |
| `POST`   | `/api/suppliers/`      | Tạo nhà cung cấp mới          | `{"code": "NCC001", "name": "Công ty ABC", "taxCode": "0123456789", "contactPerson": "Anh Tuấn", ...}`          | `{...}`                            |
| `GET`    | `/api/suppliers/{id}/` | Chi tiết 1 nhà cung cấp       | —                                                                                                               | `{...}`                            |
| `PUT`    | `/api/suppliers/{id}/` | Cập nhật nhà cung cấp         | `{"name": "...", "contactPerson": "...", "phone": "...", ...}`                                                  | `{...}`                            |
| `DELETE` | `/api/suppliers/{id}/` | Vô hiệu hóa NCC (soft delete) | —                                                                                                               | `204 No Content`                   |

## Request/Response mẫu

### `GET /api/suppliers/`

**Query params hỗ trợ:**

- `?is_active=true` — filter NCC đang hợp tác (mặc định)
- `?search=ABC` — tìm theo `name` hoặc `code`

**Response:**
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "code": "NCC001",
      "name": "Công ty TNHH Vật Liệu Xây Dựng ABC",
      "taxCode": "0123456789",
      "contactPerson": "Anh Tuấn — quản lý bán hàng",
      "phone": "0903123456",
      "email": "sales@abc-vlxd.com",
      "address": "Số 45, đường Nguyễn Huệ, TP. HCM",
      "note": "Giao hàng thứ 3-5-7, giá tốt nhưng hay giao trễ",
      "isActive": true,
      "createdAt": "2026-08-01T00:00:00+07:00",
      "updatedAt": "2026-08-01T00:00:00+07:00"
    }
  ]
}
```

### `POST /api/suppliers/`

**Request:**
```json
{
  "code": "NCC002",
  "name": "Đại lý Sắt Thép Miền Tây",
  "taxCode": "0987654321",
  "contactPerson": "Chị Hương",
  "phone": "0918123456",
  "email": "huong@satthepmientay.com",
  "address": "Quốc lộ 1A, huyện Bến Lức, Long An",
  "note": "Giá sắt tốt nhất khu vực"
}
```

**Response:** `201 Created` — giống format `GET detail`.

### `GET /api/suppliers/1/`

**Response:**
```json
{
  "id": 1,
  "code": "NCC001",
  "name": "Công ty TNHH Vật Liệu Xây Dựng ABC",
  "taxCode": "0123456789",
  "contactPerson": "Anh Tuấn — quản lý bán hàng",
  "phone": "0903123456",
  "email": "sales@abc-vlxd.com",
  "address": "Số 45, đường Nguyễn Huệ, TP. HCM",
  "note": "Giao hàng thứ 3-5-7, giá tốt nhưng hay giao trễ",
  "isActive": true,
  "createdAt": "2026-08-01T00:00:00+07:00",
  "updatedAt": "2026-08-01T00:00:00+07:00"
}
```

### `PUT /api/suppliers/1/`

**Request (partial update cũng dùng PUT):**
```json
{
  "code": "NCC001",
  "name": "Công ty TNHH Vật Liệu Xây Dựng ABC (đã đổi tên)",
  "contactPerson": "Anh Tuấn — trưởng phòng kinh doanh",
  "phone": "0903123457",
  "note": "Đổi số điện thoại, giá vẫn tốt"
}
```

**Response:** `200 OK` — full object đã cập nhật.

### `DELETE /api/suppliers/1/`

**Response:** `204 No Content`

> **Cơ chế:** Không xóa dòng trong DB. Set `is_active = False`.

## Ghi chú

- **Filter:** `is_active` (boolean), `search` (name, code)
- **Ordering:** mặc định theo `code` (alphabetical)
- **Pagination:** `PageNumberPagination`, page_size = 20
- **Router:** `DefaultRouter` register prefix `suppliers` → URL cuối: `/api/suppliers/`
- **ViewSet:** `ModelViewSet` — đủ 5 action CRUD, không cần `@action` tùy chỉnh
- **Serializer:** 1 serializer dùng chung cho list + detail + create + update (`SupplierSerializer`)
- **CamelCase:** `djangorestframework-camel-case` tự động convert snake_case ↔ camelCase trong JSON response/request
