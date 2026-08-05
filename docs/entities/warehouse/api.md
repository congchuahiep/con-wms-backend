# API Endpoints — Warehouse

## Danh sách endpoint

| Method   | Endpoint                | Mô tả                         | Request Body                                                                                            | Response                           |
| -------- | ----------------------- | ----------------------------- | ------------------------------------------------------------------------------------------------------- | ---------------------------------- |
| `GET`    | `/api/warehouses/`      | Danh sách kho                 | —                                                                                                       | `{"count": N, "results": [{...}]}` |
| `POST`   | `/api/warehouses/`      | Tạo kho mới                   | `{"code": "KHO_CHINH", "name": "Kho chính", "address": "...", "note": "...", "latitude": 10.7626, "longitude": 106.6602}` | `{...}`                            |
| `GET`    | `/api/warehouses/{id}/` | Chi tiết 1 kho                | —                                                                                                       | `{...}`                            |
| `PUT`    | `/api/warehouses/{id}/` | Cập nhật kho                  | `{"name": "...", "note": "...", "latitude": 10.7626, "longitude": 106.6602}`                            | `{...}`                            |
| `DELETE` | `/api/warehouses/{id}/` | Vô hiệu hóa kho (soft delete) | —                                                                                                       | `204 No Content`                   |

## Request/Response mẫu

### `GET /api/warehouses/`

**Query params hỗ trợ:**

- `?is_active=true` — filter kho đang hoạt động (mặc định)
- `?search=chính` — tìm theo `name` hoặc `code`

**Response:**
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "code": "KHO_CHINH",
      "name": "Kho chính — Bãi sau",
      "address": "Số 12, đường A, xã B",
      "note": "Kho chính — nền bê tông, mái tôn, có cửa cuốn",
      "latitude": 10.762622,
      "longitude": 106.660172,
      "is_active": true,
      "created_at": "2026-01-01T00:00:00+07:00",
      "updated_at": "2026-08-01T00:00:00+07:00"
    }
  ]
}
```

### `POST /api/warehouses/`

**Request:**
```json
{
  "code": "KHO_PHU",
  "name": "Kho phụ — Gần cổng",
  "address": "Đường nội bộ công ty",
  "note": "Kho phụ — nền đất, che bạt, chỉ chứa vật liệu nhẹ",
  "latitude": 10.772622,
  "longitude": 106.670172
}
```

**Response:** `201 Created` — giống format `GET detail` bên dưới.

### `GET /api/warehouses/1/`

**Response:**
```json
{
  "id": 1,
  "code": "KHO_CHINH",
  "name": "Kho chính — Bãi sau",
  "address": "Số 12, đường A, xã B",
  "note": "Kho chính — nền bê tông, mái tôn, có cửa cuốn",
  "latitude": 10.762622,
  "longitude": 106.660172,
  "is_active": true,
  "created_at": "2026-01-01T00:00:00+07:00",
  "updated_at": "2026-08-01T00:00:00+07:00"
}
```

### `PUT /api/warehouses/1/`

**Request (partial update cũng dùng PUT):**
```json
{
  "name": "Kho chính — Bãi sau (đã mở rộng)",
  "note": "Đã dọn lại mặt bằng, kê thêm 2 kệ sắt ở giữa kho",
  "latitude": 10.762700,
  "longitude": 106.660300
}
```

**Response:** `200 OK` — full object đã cập nhật.

### `DELETE /api/warehouses/1/`

**Response:** `204 No Content`

> **Cơ chế:** Không xóa dòng trong DB. Set `is_active = False`. Các phiếu nhập/xuất cũ vẫn giữ nguyên FK tới kho này.

## Ghi chú

- **Filter:** `is_active` (boolean), `search` (name, code)
- **Ordering:** mặc định theo `name` (alphabetical)
- **Pagination:** `PageNumberPagination`, page_size = 20
- **Router:** `DefaultRouter` register prefix `warehouses` → URL cuối: `/api/warehouses/`
- **ViewSet:** `ModelViewSet` — đủ 5 action CRUD, không cần `@action` tùy chỉnh
- **Serializer:** 1 serializer dùng chung cho list + detail + create + update (`WarehouseSerializer`)
- **`note` vs vị trí đặt đồ:** `note` là ghi chú về **bản thân kho** (tình trạng, lưu ý). Vị trí đặt đồ sẽ được lưu ở entity `MaterialStock` (tồn kho theo vật tư) hoặc `Location` (tương lai).
