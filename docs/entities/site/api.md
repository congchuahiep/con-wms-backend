# API Endpoints — Site (Công Trường)

## Danh sách endpoint

| Method   | Endpoint            | Mô tả                                 | Request Body                                                        | Response         |
| -------- | ------------------- | ------------------------------------- | ------------------------------------------------------------------- | ---------------- |
| `GET`    | `/api/sites/`       | Danh sách công trường đang hoạt động  | —                                                                   | `[{...}]`        |
| `POST`   | `/api/sites/`       | Tạo công trường mới                   | `{"code": "CT_RG", "name": "...", "manager": "...", ...}`           | `201`            |
| `GET`    | `/api/sites/{id}/`  | Chi tiết                              | —                                                                   | `{...}`          |
| `PUT`    | `/api/sites/{id}/`  | Sửa                                  | Giống POST                                                          | `200`            |
| `DELETE` | `/api/sites/{id}/`  | Vô hiệu hóa (soft delete)             | —                                                                   | `204 No Content` |

## Request/Response mẫu

**Request:**

```json
{
    "code": "CT_RG",
    "name": "Công trường cầu Rạch Giá",
    "manager": "Anh Bảy",
    "phone": "0901234567",
    "address": "QL80, TP Rạch Giá",
    "note": "Khu vực thi công chật, xe tải lớn khó vào"
}
```

**Response `201 Created`:**

```json
{
    "id": 1,
    "code": "CT_RG",
    "name": "Công trường cầu Rạch Giá",
    "manager": "Anh Bảy",
    "phone": "0901234567",
    "address": "QL80, TP Rạch Giá",
    "note": "Khu vực thi công chật, xe tải lớn khó vào",
    "isActive": true,
    "createdAt": "2026-08-18T09:00:00+07:00",
    "updatedAt": "2026-08-18T09:00:00+07:00"
}
```

## Query params

- `?search=...` — tìm theo mã/tên công trường
- `?is_active=true|false` — mặc định `true` (chỉ trả công trường đang thi công); `false` để xem cả đã vô hiệu hóa

Response: **không phân trang** (master data — giống Warehouse/Supplier).

## Validation rules

| Rule | Mô tả | HTTP |
|---|---|---|
| Code unique | `code` không trùng công trường khác | 400 |
| Name required | `name` bắt buộc | 400 |
| Soft delete | `DELETE` → `is_active=false`, không xóa cứng | 204 |

## Ghi chú

- Master data — write chỉ admin, mọi role đọc được (xem [`auth.md`](auth.md))
- Công trường đang được phiếu tham chiếu **không xóa cứng được** (FK PROTECT) — chỉ vô hiệu hóa
- Sau này `OutboundNote` (xuất cấp) và có thể `InboundNote` (trả lại) dùng `site` FK này để **báo cáo theo công trường**: `?site=1` trên `/api/outbound-notes/`, lọc sổ kho qua `outbound_note__site`
