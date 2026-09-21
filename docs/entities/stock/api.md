# API Endpoints — Stock (Tồn kho & Sổ kho)

> Tất cả endpoint đều **read-only** — không có API ghi trực tiếp (model.md D9).
> Dòng sổ kho chỉ thay đổi qua hành động chốt/hủy phiếu ở các entity phiếu.

## Danh sách endpoint

| Method | Endpoint                | Mô tả                            |
| ------ | ----------------------- | -------------------------------- |
| `GET`  | `/api/stock/`           | Tồn kho hiện tại theo kho+vật tư |
| `GET`  | `/api/stock/movements/` | Sổ kho — lịch sử các dòng ghi    |

## 1. `GET /api/stock/` — Tồn kho hiện tại

**Query params:**

- `?warehouse=1` — lọc theo kho (bỏ trống = tất cả kho)
- `?material=1` — lọc theo vật tư
- `?category=1` — lọc theo nhóm vật tư
- `?search=XM` — tìm theo mã/tên vật tư
- `?has_stock=true` — chỉ lấy vật tư còn tồn (quantity ≠ 0)

**Response:** danh sách phẳng, **không phân trang** (số dòng = số vật tư × số kho, quy mô nhỏ):

```json
[
    {
        "material": { "id": 1, "code": "XM_PCB40", "name": "Xi măng PCB40" },
        "unit": { "id": 2, "code": "BAO", "name": "Bao" },
        "warehouse": {
            "id": 1,
            "code": "KHO_CHINH",
            "name": "Kho chính — Bãi sau"
        },
        "quantity": "85.000",
        "lastPurchasePrice": "88000.00",
        "stockValue": "7480000.00"
    }
]
```

**Cách tính:**

| Field               | Cách tính                                                                                          |
| ------------------- | -------------------------------------------------------------------------------------------------- |
| `quantity`          | `SUM(quantity)` các dòng sổ kho theo `(warehouse, material)`                                       |
| `lastPurchasePrice` | `unit_price` của dòng `inbound_purchase_from_supplier` mới nhất (theo `date`, `id`); null nếu chưa từng nhập mua |
| `stockValue`        | `quantity × lastPurchasePrice` (null nếu giá null)                                                 |

## 2. `GET /api/stock/movements/` — Sổ kho

**Query params:**

- `?material=1` / `?warehouse=1` — lọc theo vật tư / kho
- `?movement_type=inbound_purchase_from_supplier` — lọc theo loại dòng
- `?date_from=2026-08-01&date_to=2026-08-31` — lọc theo **ngày nghiệp vụ**
- `?inbound_note=1` — xem sổ kho của 1 phiếu
- `?originals_only=true` — ẩn dòng reversal (mặc định true)

**Response:** phân trang chuẩn của project (`items`/`meta`), `pageSize=50`, sắp xếp `-date, -id`:

```json
{
  "items": [
    {
      "id": 12,
      "movementType": "inbound_purchase_from_supplier",
      "movementTypeLabel": "Nhập kho: mua hàng từ nhà cung cấp",
      "date": "2026-08-13",
      "material": {
        "id": 1,
        "code": "XM_PCB40",
        "name": "Xi măng PCB40"
      },
      "warehouse": {
        "id": 1,
        "code": "KHO_CHINH",
        "name": "Kho chính — Bãi sau"
      },
      "quantity": "100.000",
      "unitPrice": "88000.00",
      "sourceNote": { "id": 3, "number": "PN-20260813-001", "noteType": "inbound" },
      "reversalOf": null,
      "reason": "",
      "createdBy": { "id": 2, "email": "thukho@test.com" },
      "createdAt": "2026-08-13T08:30:00+07:00"
    }
  ],
  "meta": {
    "page": 1,
    "pageSize": 50,
    "total": 128,
    "totalPages": 3,
    "hasNextPage": true,
    "hasPreviousPage": false
  }
}
```

## Field `sourceNote` — phiếu nguồn của dòng sổ kho (v1.6)

Mỗi dòng sổ kho trả đúng **1** field `sourceNote` (thay cho 3 field
`inboundNote` / `outboundNote` / `stocktakeNote` cũ):

```jsonc
"sourceNote": { "id": 3, "number": "PN-20260813-001", "noteType": "inbound" }
```

| `movementType` | `sourceNote.noteType` | Phiếu nguồn |
|---|---|---|
| `inbound_purchase_from_supplier` | `inbound` | Phiếu nhập (`purchase`) |
| `inbound_return_from_site` | `inbound` | Phiếu nhập (`return_from_site`) |
| `outbound_issue_for_use` | `outbound` | Phiếu xuất (`issue_for_use`) |
| `outbound_transfer_to_warehouse` | `outbound` | Phiếu xuất điều chuyển — dòng xuất ở **kho nguồn** |
| `inbound_transfer_from_warehouse` | `outbound` | **CÙNG phiếu xuất điều chuyển** — dòng nhập ở **kho đích** |
| `stocktake_adjustment` | `stocktake` | Phiếu kiểm kê |
| Dòng reversal (`reversalOf != null`) | như dòng gốc | Cùng phiếu nguồn của dòng gốc (phiếu đã hủy) |

`noteType` do backend suy từ FK nguồn thực tế (`inbound_note` / `outbound_note` /
`stocktake_note` — bất biến `ck_sm_exactly_one_source`), **không** phải map ngược từ
`movementType`. Hiện mọi dòng đều có phiếu nguồn; field giữ `null`-able để tương lai
mở rộng (dòng điều chỉnh không thuộc phiếu nào).

## Validation rules

| Rule                  | Mô tả                                     | HTTP                 |
| --------------------- | ----------------------------------------- | -------------------- |
| Read-only             | Mọi method khác `GET` trên 2 endpoint     | 405                  |
| Bút toán đúng 1 nguồn | Dòng sổ kho phải thuộc đúng 1 phiếu nguồn | (DB CheckConstraint) |

## Ghi chú

- **Không có endpoint write** — nếu thủ kho cần "thêm hàng" thì lập phiếu nhập; cần "bớt hàng" thì lập phiếu xuất hoặc phiếu kiểm kê (điều chỉnh có lý do).
- `lastPurchasePrice` bỏ qua dòng hoàn trả (không có giá) — luôn là giá nhập mua gần nhất.
- Router: `DefaultRouter` register `stock` (balance) + `stock-movements` (sổ kho) trong app `inventory` → URL cuối: `/api/stock/`, `/api/stock/movements/`.
