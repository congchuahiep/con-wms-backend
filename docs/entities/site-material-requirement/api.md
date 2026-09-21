# API — Site Material Requirement (Định mức vật tư công trường)

> Router: `sites/urls.py` — `SiteViewSet` thêm 2 action (`requirements`, `settle`) + thay đổi `list`/detail.
> Ký hiệu dữ liệu vào/ra theo convention repo: **camelCase** (djangorestframework-camel-case).

## 1. `GET /api/sites/` + `GET /api/sites/{id}/` — đổi `is_active` → `status`

Response mỗi công trường (thay field `is_active`):

```json
{
    "id": 1,
    "code": "CT_RG",
    "name": "Công trường cầu Rạch Giá",
    "status": "active",
    "statusLabel": "Đang hoạt động",
    "settledAt": null,
    "settledBy": null,
    "warehouse": { "id": 4, "code": "KHO_CT_RG", "name": "Công trường cầu Rạch Giá" }
}
```

- Query param `list` đổi `is_active=true/false` → **`?status=active|completed|inactive|all`** (mặc định `active` — giữ hành vi cũ là chỉ trả đang hoạt động).
- `DELETE /api/sites/{id}/` vẫn soft-delete như cũ nhưng đặt `status=inactive` (thay `is_active=False`).
- **Không còn `isActive` trong mọi response site** → frontend cập nhật type theo.

## 2. `GET /api/sites/{id}/requirements/` — bảng so sánh định mức vs tồn kho

Response: mảng dòng — **hợp của** (a) mọi vật tư có định mức + (b) mọi vật tư tồn > 0 trong kho công trường; sort định mức trước, theo mã vật tư.

```json
[
    {
        "material": { "id": 1, "code": "XM", "name": "Xi măng PCB40", "unitCode": "BAO" },
        "requiredQuantity": "3.000",
        "balance": "5.000",
        "status": "sufficient",
        "defaultReturnQuantity": "2.000",
        "note": ""
    },
    {
        "material": { "id": 2, "code": "GACH", "name": "Gạch ống 2 lỗ", "unitCode": "VIEN" },
        "requiredQuantity": "20000.000",
        "balance": "10000.000",
        "status": "insufficient",
        "defaultReturnQuantity": "0.000",
        "note": ""
    },
    {
        "material": { "id": 9, "code": "MAYKHOAN", "name": "Máy khoan bê tông", "unitCode": "CAI" },
        "requiredQuantity": null,
        "balance": "1.000",
        "status": "not_in_plan",
        "defaultReturnQuantity": "1.000",
        "note": null
    }
]
```

| Field                    | Kiểu            | Ý nghĩa                                                                                  |
| ------------------------ | --------------- | ---------------------------------------------------------------------------------------- |
| `requiredQuantity`       | string\|null    | Định mức (Decimal 14,3 dạng chuỗi); `null` nếu ngoài định mức                           |
| `balance`                | string          | Tồn kho hiện tại của kho công trường = SUM sổ kho theo `(warehouse, material)`           |
| `status`                 | string          | `sufficient` / `insufficient` / `not_in_plan` (xem model.md §3.2)                        |
| `defaultReturnQuantity`  | string          | Số lượng mặc định trả về khi tất toán: `max(balance − required, 0)`; ngoài định mức = `balance` |

> Decimal trả dạng **string** (giống `StockBalance` frontend hiện có) — frontend không tính toán số thực.

## 3. `PUT /api/sites/{id}/requirements/` — thay toàn bộ định mức

Body:

```json
{
    "lines": [
        { "materialId": 1, "quantity": "3.000", "note": "Cho cọc móng đợt 1" },
        { "materialId": 2, "quantity": "20000.000" }
    ]
}
```

- Semantics: **bulk replace** — xóa hết dòng cũ, tạo lại theo `lines` (một transaction) — "chỉnh sửa nhanh" như user yêu cầu; `lines` rỗng = xóa toàn bộ định mức.
- Validation:
  - `site.status == active` (đã tất toán/ngừng → 400).
  - Mỗi dòng: `materialId` tồn tại, `quantity > 0`, không trùng vật tư trong cùng request.
  - Dòng trùng `(site, material)` đã có → bị replace (bulk) — không cần endpoint xóa riêng.
- Response: 200 + mảng định mức mới (dạng `§2` nhưng không cần `balance`/`status`).

## 4. `POST /api/sites/{id}/settle/` — Tất toán

Body:

```json
{
    "toWarehouseId": 1,
    "lines": [
        { "materialId": 1, "quantity": "2.000", "note": "2 bao xi bị ẩm, giữ lại xử lý" },
        { "materialId": 9, "quantity": "1.000" }
    ]
}
```

- `lines[].note` (tùy chọn): **bắt buộc ghi khi `quantity` < giá trị mặc định `defaultReturnQuantity`** (lý do giảm số lượng); lưu vào `OutboundNoteLine.note` của phiếu tất toán (user chốt bổ sung 2026-09-20).

Validation (thứ tự):
1. `site.status == active` — đã completed/inactive → 400 `"Công trường đã đóng."`
2. **Mọi dòng định mức có `balance >= requiredQuantity`** (tính lại từ sổ kho tại thời điểm thực thi) → nếu thiếu bất kỳ dòng nào: 400 kèm danh sách `materialId` thiếu.
3. `toWarehouseId`: tồn tại, `is_active=True`, ≠ kho công trường của site này.
4. `lines`: không rỗng; mỗi dòng `materialId` có tồn > 0 ở kho công trường; `0 < quantity <= balance`; không trùng vật tư.

Hành vi (atomic):

- Tạo `OutboundNote(note_type=transfer, warehouse=kho CT, to_warehouse=kho đích, note="Tất toán công trường <code> — <tên>", created_by=user)` + dòng vật tư → `note.post(user)` (chốt ngay, sinh 2 dòng sổ kho/dòng).
- `site.status=completed`, `settled_at=now`, `settled_by=user`.
- `site.warehouse.is_active=False` (đóng kho).

Response 200:

```json
{
    "site": {
        "id": 1, "code": "CT_RG", "name": "Công trường cầu Rạch Giá",
        "status": "completed", "statusLabel": "Đã hoàn thành",
        "settledAt": "2026-09-20T10:00:00Z",
        "settledBy": { "id": 1, "name": "Admin" }
    },
    "outboundNote": {
        "id": 123, "number": "PX-20260920-001", "status": "posted",
        "warehouse": { "id": 4, "code": "KHO_CT_RG", "name": "..." },
        "toWarehouse": { "id": 1, "code": "KHO_CHINH", "name": "Kho chính" },
        "lines": [ { "material": { "id": 1, "code": "XM", "name": "Xi măng PCB40", "unitCode": "BAO" }, "quantity": "2.000", "note": "2 bao xi bị ẩm, giữ lại xử lý" } ]
    }
}
```

## 5. Backend — guard chặn phiếu vào kho đã đóng (không phải endpoint mới)

| Vị trí                                    | Thay đổi                                                                                          |
| ----------------------------------------- | ------------------------------------------------------------------------------------------------- |
| `inventory/models.py` `BaseNote.post()` / `void()` | Đầu hàm: `warehouse.is_active == False` hoặc `warehouse.site.status != active` → `ValidationError` "Kho đã đóng." |
| `InboundNoteSerializer.validate()`        | Khi tạo/sửa: kiểm tra `warehouse` mở (như trên) → 400 sớm                                        |
| `OutboundNoteSerializer.validate()`       | Kiểm tra `warehouse` mở + `to_warehouse` mở (điều chuyển) → 400 sớm                              |
| `StocktakeNoteSerializer.validate()`      | Kiểm tra `warehouse` mở → 400 sớm                                                                |

## 6. Không thay đổi

- `OutboundNote` transfer / `InboundNote` / `StocktakeNote` endpoints — giữ nguyên (settlement tái sử dụng transfer).
- `StockBalanceViewSet` (`/api/stock/`) — giữ nguyên; bảng so sánh dùng logic riêng gọn hơn (đã gộp định mức + tồn).