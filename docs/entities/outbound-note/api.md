# API Endpoints — Outbound Note

## Danh sách endpoint

| Method   | Endpoint                          | Mô tả                              | Request Body                                                                                            | Response                     |
| -------- | --------------------------------- | ---------------------------------- | ------------------------------------------------------------------------------------------------------- | ---------------------------- |
| `GET`    | `/api/outbound-notes/`            | Danh sách phiếu xuất (phân trang)  | —                                                                                                       | `{"items": [...], "meta": {...}}` |
| `POST`   | `/api/outbound-notes/`            | Tạo phiếu **nháp** + dòng          | `{"noteType": "issue_for_use", "date": "2026-08-18", "warehouseId": 1, "siteId": 1, "lines": [...]}` | `201` (status=`draft`)      |
| `GET`    | `/api/outbound-notes/{id}/`       | Chi tiết phiếu + dòng              | —                                                                                                       | `{...}`                      |
| `PUT`    | `/api/outbound-notes/{id}/`       | Sửa phiếu **nháp** (replace-all)   | Giống POST                                                                                              | `200`                        |
| `DELETE` | `/api/outbound-notes/{id}/`       | Xóa cứng phiếu **nháp**            | —                                                                                                       | `204 No Content`             |
| `POST`   | `/api/outbound-notes/{id}/post/`  | **Chốt** → check tồn + ghi sổ kho  | —                                                                                                       | `200` (status=`posted`)     |
| `POST`   | `/api/outbound-notes/{id}/void/`  | **Hủy** → dòng sổ kho ngược dấu    | `{"reason": "Xuất nhầm số lượng"}`                                                                      | `200` (status=`voided`)     |

## Request/Response mẫu

### `POST /api/outbound-notes/` — tạo phiếu xuất cấp (nháp)

**Request:**

```json
{
    "noteType": "issue_for_use",
    "date": "2026-08-18",
    "warehouseId": 1,
    "siteId": 1,
    "note": "Cấp xi măng cho đổ móng",
    "lines": [
        { "materialId": 1, "quantity": "50" },
        { "materialId": 2, "quantity": "2.5" }
    ]
}
```

**Response `201 Created`** (rút gọn):

```json
{
    "id": 1,
    "number": "PX-20260818-001",
    "noteType": "issue_for_use",
    "noteTypeLabel": "Xuất cấp cho công trường sử dụng",
    "status": "draft",
    "statusLabel": "Nháp",
    "date": "2026-08-18",
    "warehouse": { "id": 1, "code": "KHO_CHINH", "name": "Kho chính — Bãi sau" },
    "toWarehouse": null,
    "site": { "id": 1, "code": "CT_RG", "name": "Công trường cầu Rạch Giá" },
    "createdBy": { "id": 2, "email": "thukho@test.com" },
    "totalQuantity": 2,
    "lines": [ "...2 dòng: material, quantity, lineNo, note..." ]
}
```

> **Không có `totalAmount`** — phiếu xuất không có giá.

### `POST /api/outbound-notes/` — tạo phiếu điều chuyển (nháp)

```json
{
    "noteType": "transfer",
    "date": "2026-08-18",
    "warehouseId": 1,
    "toWarehouseId": 2,
    "siteId": null,
    "lines": [ { "materialId": 1, "quantity": "30" } ]
}
```

### `POST /api/outbound-notes/1/post/` — chốt phiếu

**Response `200 OK`:** status=`posted`. Đồng thời hệ thống ghi sổ kho:

- `issue_for_use` → 1 dòng `outbound_issue_for_use` (−quantity) / dòng phiếu
- `transfer` → 2 dòng: `outbound_transfer_to_warehouse` (−, kho đi) + `inbound_transfer_from_warehouse` (+, kho đến) / dòng phiếu

Thiếu tồn → `400` kèm mã vật tư thiếu (không chốt, không ghi gì).

### `POST /api/outbound-notes/1/void/` — hủy phiếu

**Request:** `{ "reason": "Xuất nhầm số lượng" }`

**Response `200 OK`:** status=`voided`, kèm `voidedBy`, `voidedAt`, `voidReason`. Hệ thống ghi dòng ngược dấu cho mọi dòng gốc — tồn kho trở về như trước phiếu.

## Query params (list)

- `?note_type=issue_for_use|transfer` — lọc theo loại phiếu
- `?status=draft|posted|voided` — lọc theo trạng thái
- `?warehouse=1` — lọc theo kho xuất
- `?to_warehouse=1` — lọc theo kho đích
- `?site=1` — lọc theo công trường nhận hàng
- `?date_from=2026-08-01&date_to=2026-08-31` — lọc theo khoảng ngày
- `?search=...` — tìm theo số phiếu / ghi chú / nơi nhận

Response: phân trang chuẩn project (`page_size=20`), mỗi item là phiếu **không kèm lines** (list gọn — chi tiết mới lấy lines).

## Validation rules

| Rule                  | Mô tả                                                    | HTTP |
| --------------------- | -------------------------------------------------------- | ---- |
| Site required         | `noteType=issue_for_use` mà thiếu `siteId`               | 400  |
| Site forbidden        | `noteType=transfer` mà có `siteId`                       | 400  |
| toWarehouse required  | `noteType=transfer` mà thiếu `toWarehouseId`             | 400  |
| toWarehouse forbidden | `noteType=issue_for_use` mà có `toWarehouseId`           | 400  |
| Kho đích ≠ kho xuất   | `toWarehouseId` trùng `warehouseId`                      | 400  |
| Quantity > 0          | Mỗi dòng `quantity` phải > 0                             | 400  |
| Lines required        | Phiếu phải có ít nhất 1 dòng                             | 400  |
| Đủ tồn                | `/post/` khi tồn `(kho, vật tư)` < từng dòng             | 400  |
| Chốt phiếu nháp       | `/post/` chỉ khi `status=draft`                          | 400  |
| Hủy cần lý do         | `/void/` bắt buộc `reason`                               | 400  |
| Hủy phiếu đã chốt     | `/void/` chỉ khi `status=posted`                         | 400  |
| Phiếu bất biến        | PUT/DELETE khi `posted`/`voided`                         | 400  |

## Ghi chú

- **Number:** tự sinh server-side khi tạo, read-only. Format `PX-YYYYMMDD-NNN` (sequence riêng của phiếu xuất)
- **`createdBy` / `voidedBy`:** tự set từ `request.user`, read-only
- **`totalQuantity`:** **số dòng vật tư** (integer) — cùng quy ước với InboundNote
- **`site`:** công trường nhận hàng — chọn từ `/api/sites/` (master data, xem [`../site/`](../site/README.md)); bắt buộc khi xuất cấp, null khi điều chuyển
- **Nested write:** `transaction.atomic` — hoặc tạo cả phiếu + dòng, hoặc fail toàn bộ
- **Update lines:** strategy replace-all (xóa dòng cũ, tạo lại) — chỉ khi draft
- **Chốt/hủy:** `BaseNote.post()` / `BaseNote.void()` + hook riêng của `OutboundNote` (xem [`model.md`](model.md) §5-6)
- **Sổ kho:** dòng xuất trỏ `outboundNote` trên `GET /api/stock/movements/` (xem [`../stock/api.md`](../stock/api.md))
