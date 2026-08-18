# API Endpoints — Inbound Note

## Danh sách endpoint

| Method   | Endpoint                       | Mô tả                              | Request Body                                                                                        | Response                     |
| -------- | ------------------------------ | ---------------------------------- | --------------------------------------------------------------------------------------------------- | ---------------------------- |
| `GET`    | `/api/inbound-notes/`          | Danh sách phiếu nhập               | —                                                                                                   | `{"items": [...], "meta": {...}}` |
| `POST`   | `/api/inbound-notes/`          | Tạo phiếu **nháp** + dòng          | `{"noteType": "purchase", "date": "2026-08-13", "warehouseId": 1, "supplierId": 1, "lines": [...]}` | `201` (status=`draft`)      |
| `GET`    | `/api/inbound-notes/{id}/`     | Chi tiết phiếu + dòng              | —                                                                                                   | `{...}`                      |
| `PUT`    | `/api/inbound-notes/{id}/`     | Sửa phiếu **nháp** (replace-all)   | Giống POST                                                                                          | `200`                        |
| `DELETE` | `/api/inbound-notes/{id}/`     | Xóa cứng phiếu **nháp**            | —                                                                                                   | `204 No Content`             |
| `POST`   | `/api/inbound-notes/{id}/post/` | **Chốt phiếu** → ghi sổ kho        | —                                                                                                   | `200` (status=`posted`)     |
| `POST`   | `/api/inbound-notes/{id}/void/` | **Hủy phiếu** → dòng sổ kho ngược dấu | `{"reason": "Nhập sai số lượng"}`                                                              | `200` (status=`voided`)     |

## Request/Response mẫu

### `POST /api/inbound-notes/` — tạo phiếu nháp

**Request** (tạo phiếu nhập mua — thủ kho quét 2 dòng):

```json
{
    "noteType": "purchase",
    "date": "2026-08-13",
    "warehouseId": 1,
    "supplierId": 1,
    "note": "Nhập xi măng + cát cho công trình cầu Rạch Giá",
    "lines": [
        { "materialId": 1, "quantity": "100", "unitPrice": "88000", "note": "Bao 50kg" },
        { "materialId": 2, "quantity": "5.5", "unitPrice": "350000", "note": "" }
    ]
}
```

**Response `201 Created`** (rút gọn):

```json
{
    "id": 1,
    "number": "PN-20260813-001",
    "noteType": "purchase",
    "noteTypeLabel": "Mua hàng từ nhà cung cấp",
    "status": "draft",
    "statusLabel": "Nháp",
    "date": "2026-08-13",
    "warehouse": { "id": 1, "code": "KHO_CHINH", "name": "Kho chính — Bãi sau" },
    "supplier": { "id": 1, "code": "NCC001", "name": "Công ty TNHH Vật Liệu Xây Dựng ABC" },
    "createdBy": { "id": 2, "email": "thukho@test.com" },
    "totalAmount": "10725000",
    "totalQuantity": 2,
    "lines": [ "...2 dòng như cũ..." ]
}
```

### `POST /api/inbound-notes/1/post/` — chốt phiếu

**Request:** (không body)

**Response `200 OK`:** phiếu với `status: "posted"`. Đồng thời hệ thống đã ghi 2 dòng sổ kho (`+100` xi măng, `+5.5` cát) — tồn kho `/api/stock/` tăng ngay lập tức.

### `POST /api/inbound-notes/1/void/` — hủy phiếu

**Request:**

```json
{ "reason": "Nhập sai số lượng, NCC giao thiếu" }
```

**Response `200 OK`:** phiếu với `status: "voided"`, `voidedBy`, `voidedAt`, `voidReason`. Tồn kho tự trừ ngược lại (`−100` xi măng, `−5.5` cát).

### `GET /api/inbound-notes/`

**Query params hỗ trợ:**

- `?note_type=purchase|return_from_site` — lọc theo loại phiếu
- `?status=draft|posted|voided` — lọc theo trạng thái
- `?warehouse=1` — lọc theo kho
- `?supplier=1` — lọc theo NCC
- `?date_from=2026-08-01&date_to=2026-08-31` — lọc theo khoảng ngày
- `?search=PN-2026` — tìm theo số phiếu

**Response:** format phân trang chuẩn của project (`config.pagination.StandardPageNumberPagination`) — mỗi item là phiếu **không kèm lines** (list gọn, chi tiết mới lấy lines):

```json
{
  "items": [
    {
      "id": 1,
      "number": "PN-20260813-001",
      "noteType": "purchase",
      "noteTypeLabel": "Mua hàng từ nhà cung cấp",
      "status": "posted",
      "statusLabel": "Đã chốt",
      "date": "2026-08-13",
      "warehouse": { "id": 1, "code": "KHO_CHINH", "name": "Kho chính — Bãi sau" },
      "supplier": { "id": 1, "code": "NCC001", "name": "Công ty TNHH Vật Liệu Xây Dựng ABC" },
      "createdBy": { "id": 2, "email": "thukho@test.com" },
      "totalAmount": "10725000.00",
      "totalQuantity": 2,
      "createdAt": "2026-08-13T08:30:00+07:00",
      "updatedAt": "2026-08-13T08:30:00+07:00"
    }
  ],
  "meta": {
    "page": 1,
    "pageSize": 20,
    "total": 1,
    "totalPages": 1,
    "hasNextPage": false,
    "hasPreviousPage": false
  }
}
```

### `PUT /api/inbound-notes/1/`

Chỉ áp dụng khi `status=draft`. Request giống POST; các dòng cũ bị xóa và thay bằng danh sách mới (replace-all). Phiếu `posted`/`voided` → `400`.

### `DELETE /api/inbound-notes/1/`

Chỉ áp dụng khi `status=draft` — xóa cứng phiếu + dòng (chưa có dòng sổ kho nên an toàn). Phiếu `posted`/`voided` → `400` (dùng `/void/` thay thế).

## Validation rules

| Rule               | Mô tả                                       | HTTP |
| ------------------ | ------------------------------------------- | ---- |
| Supplier required  | `note_type=purchase` mà thiếu `supplier`    | 400  |
| Supplier forbidden | `note_type=return_from_site` mà có `supplier` | 400  |
| Lines required     | Phiếu phải có ít nhất 1 dòng                | 400  |
| Quantity > 0       | Mỗi dòng `quantity` phải > 0                | 400  |
| Unit price >= 0    | Mỗi dòng `unitPrice` phải >= 0              | 400  |
| Material tồn tại   | `materialId` phải tồn tại (PROTECT khi xóa) | 400/409 |
| Chốt phiếu nháp    | `/post/` chỉ khi `status=draft`             | 400  |
| Hủy cần lý do      | `/void/` bắt buộc `reason`                  | 400  |
| Hủy phiếu đã chốt  | `/void/` chỉ khi `status=posted`            | 400  |
| Phiếu bất biến     | PUT/DELETE khi `posted`/`voided`            | 400  |

## Ghi chú

- **Number:** tự sinh server-side khi tạo, read-only. Format `PN-YYYYMMDD-NNN` (NNN = sequence trong ngày)
- **`createdBy` / `voidedBy`:** tự set từ `request.user`, read-only — thủ kho không thể giả mạo
- **`totalAmount`:** tính động = Σ(quantity × unit_price), không lưu DB
- **`totalQuantity`:** **số dòng vật tư** của phiếu (integer), không phải tổng số lượng — tổng số lượng lấy từ từng dòng `lines[].quantity`
- **Nested write:** `transaction.atomic` — hoặc tạo cả phiếu + dòng, hoặc fail toàn bộ
- **Update lines:** strategy replace-all (xóa dòng cũ, tạo lại) — chỉ khi draft
- **Chốt/hủy ghi sổ kho:** logic vòng đời đặt ở `BaseNote.post()` / `BaseNote.void()` trong `inventory/models.py` (xem [`stock/implementation.md`](../stock/implementation.md)), cùng `transaction.atomic` với việc đổi `status`
- **Router:** `DefaultRouter` register prefix `inbound-notes` → URL cuối: `/api/inbound-notes/`; 2 action `post`, `void` map bằng `@action(detail=True, methods=["post"])`
