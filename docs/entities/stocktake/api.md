# API Endpoints — Stocktake Note

## Danh sách endpoint

| Method   | Endpoint                          | Mô tả                                  | Request Body                                                                                                  | Response                          |
| -------- | --------------------------------- | -------------------------------------- | ------------------------------------------------------------------------------------------------------------- | --------------------------------- |
| `GET`    | `/api/stocktake-notes/`           | Danh sách phiếu kiểm kê (phân trang)   | —                                                                                                             | `{"items": [...], "meta": {...}}` |
| `POST`   | `/api/stocktake-notes/`           | Tạo phiếu **nháp** kèm dòng chênh lệch | `{"date": "2026-08-18", "warehouseId": 1, "lines": [{"materialId": 1, "difference": "-3", "reason": "..."}]}` | `201` (status=`draft`)            |
| `GET`    | `/api/stocktake-notes/{id}/`      | Chi tiết phiếu + dòng                  | —                                                                                                             | `{...}`                           |
| `PUT`    | `/api/stocktake-notes/{id}/`      | Sửa phiếu **nháp** (replace-all)       | Giống POST                                                                                                    | `200`                             |
| `DELETE` | `/api/stocktake-notes/{id}/`      | Xóa cứng phiếu **nháp**                | —                                                                                                             | `204 No Content`                  |
| `POST`   | `/api/stocktake-notes/{id}/post/` | **Chốt** → ghi dòng điều chỉnh tồn     | —                                                                                                             | `200` (status=`posted`)           |
| `POST`   | `/api/stocktake-notes/{id}/void/` | **Hủy** → đảo dấu các dòng điều chỉnh  | `{"reason": "Kiểm đếm nhầm"}`                                                                                 | `200` (status=`voided`)           |

## Request/Response mẫu

### `POST /api/stocktake-notes/` — tạo phiếu kiểm kê kèm chênh lệch

**Request** — client đã đối chiếu tồn hiện tại (`/api/stock/`) với số đếm thực tế, gửi thẳng các chênh lệch:

```json
{
    "date": "2026-08-18",
    "warehouseId": 1,
    "note": "Kiểm kê cuối tháng",
    "lines": [
        { "materialId": 1, "difference": "-3", "reason": "3 bao rách vỡ" },
        {
            "materialId": 2,
            "difference": "1",
            "reason": "Tự dưng tìm thấy thứ này ngoài đường"
        }
    ]
}
```

> `difference` **có dấu**: âm = thiếu (sổ nhiều hơn thực tế), dương = thừa (thực tế nhiều hơn sổ). Không có dòng nào `difference = 0`.

**Response `201 Created`** (rút gọn):

```json
{
    "id": 1,
    "number": "PK-20260818-001",
    "status": "draft",
    "statusLabel": "Nháp",
    "date": "2026-08-18",
    "warehouse": {
        "id": 1,
        "code": "KHO_CHINH",
        "name": "Kho chính — Bãi sau"
    },
    "createdBy": { "id": 2, "email": "thukho@test.com" },
    "totalQuantity": 2,
    "lines": [
        {
            "id": 1,
            "material": {
                "id": 1,
                "code": "XM_PCB40",
                "name": "Xi măng PCB40"
            },
            "difference": "-3.000",
            "reason": "3 bao rách vỡ"
        },
        {
            "id": 2,
            "material": { "id": 2, "code": "CAT_VANG", "name": "Cát vàng" },
            "difference": "1.000",
            "reason": "Tự dưng tìm thấy thứ này ngoài đường"
        }
    ]
}
```

### `PUT /api/stocktake-notes/1/` — sửa phiếu nháp

Replace-all lines (giống các phiếu khác) — thủ kho sửa số chênh lệch / lý do trước khi chốt.

### `POST /api/stocktake-notes/1/post/` — chốt phiếu

**Response `200 OK`:** status=`posted`. Hệ thống ghi sổ kho **1 dòng cho mỗi dòng phiếu**:

- `movement_type = stocktake_adjustment`
- `quantity = difference` (âm = thiếu, dương = thừa)
- `reason` copy từ dòng

Lỗi khi chốt:

- Có dòng `difference ≠ 0` thiếu `reason` → `400`
- `difference` làm tồn âm (vd `difference = -150` trong khi kho chỉ có 100) → `400` — server tính lại tồn hiện tại **tại thời điểm chốt** từ sổ kho

### `POST /api/stocktake-notes/1/void/` — hủy phiếu

**Request:** `{ "reason": "Kiểm đếm nhầm" }`

**Response `200 OK`:** status=`voided`. Đảo dấu mọi dòng điều chỉnh đã ghi — tồn trở về giá trị sổ trước kiểm kê.

## Query params (list)

- `?status=draft|posted|voided`
- `?warehouse=1`
- `?date_from=2026-08-01&date_to=2026-08-31`
- `?search=...` — tìm theo số phiếu / ghi chú

Response: phân trang chuẩn (`page_size=20`), item không kèm lines (list gọn — chi tiết mới lấy lines).

## Validation rules

| Rule                | Mô tả                                                                    | HTTP |
| ------------------- | ------------------------------------------------------------------------ | ---- |
| Lines required      | Phiếu phải có ít nhất 1 dòng                                             | 400  |
| Difference required | Mỗi dòng phải có `difference`                                            | 400  |
| Difference ≠ 0      | Dòng `difference = 0` không hợp lệ (không điều chỉnh thì không ghi dòng) | 400  |
| Reason required     | Chốt khi dòng có `difference ≠ 0` mà thiếu `reason`                      | 400  |
| Chênh lệch vượt tồn | Chốt khi `difference < −tồn hiện tại` (tồn âm — bắt nhầm dấu/số)         | 400  |
| Chốt phiếu nháp     | `/post/` chỉ khi `status=draft`                                          | 400  |
| Hủy cần lý do       | `/void/` bắt buộc `reason`                                               | 400  |
| Hủy phiếu đã chốt   | `/void/` chỉ khi `status=posted`                                         | 400  |
| Phiếu bất biến      | PUT/DELETE khi `posted`/`voided`                                         | 400  |

## Ghi chú

- **Number:** tự sinh server-side, read-only. Format `PK-YYYYMMDD-NNN` (sequence riêng)
- **Không lưu "số trên sổ" / "số đếm được"** — phiếu chỉ chứa `difference` + `reason` (model.md D1). Client lấy tồn hiện tại từ `GET /api/stock/?warehouse=X` để làm bảng đối chiếu (số động, không lưu)
- **`totalQuantity`:** số dòng vật tư (integer) — cùng quy ước InboundNote/OutboundNote
- **Chốt/hủy:** `BaseNote.post()` / `BaseNote.void()` + hook riêng của `StocktakeNote` (check tồn + reason, sinh dòng điều chỉnh)
- **Sổ kho:** dòng điều chỉnh trỏ `stocktakeNote` trên `GET /api/stock/movements/`
