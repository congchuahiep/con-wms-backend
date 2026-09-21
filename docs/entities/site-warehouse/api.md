# API — Site Warehouse (Kho Công Trường)

> Không thêm endpoint mới — chỉ **mở rộng response** của Site và Warehouse + thay đổi cách frontend dùng dữ liệu.

## 1. `GET /api/sites/` (SiteViewSet)

Response mỗi công trường thêm field `warehouse` (read-only, trả kèm khi lấy):

```json
{
    "id": 1,
    "code": "CT_RG",
    "name": "Công trường cầu Rạch Giá",
    "manager": "...",
    "is_active": true,
    "warehouse": {
        "id": 4,
        "code": "KHO_CT_RG",
        "name": "Công trường cầu Rạch Giá"
    }
}
```

- **`POST /api/sites/`**: tạo công trường → signal tự tạo kho → response trả kèm `warehouse` luôn.
- **`PUT/PATCH /api/sites/{id}/`**: không tạo lại kho (signal chỉ chạy khi `created=True`).
- **`DELETE /api/sites/{id}/`**: soft-delete (`is_active=False`) — kho công trường **giữ nguyên** (không bị xóa theo).

## 2. `GET /api/warehouses/` (WarehouseViewSet)

> **Mặc định chỉ trả kho trung tâm** (`site = null`). Truyền **`?include_site=true`** để lấy cả kho công trường (dropdown chọn kho khi lập phiếu, lọc sổ kho...).

Response mỗi kho thêm field `site` (read-only, `null` với kho thường):

```json
{
    "id": 1,
    "code": "KHO_CHINH",
    "name": "Kho chính — Bãi sau",
    "site": null
}
```

```json
{
    "id": 4,
    "code": "KHO_CT_RG",
    "name": "Công trường cầu Rạch Giá",
    "site": { "id": 1, "code": "CT_RG", "name": "Công trường cầu Rạch Giá" }
}
```

- Frontend dùng `site` để: (1) nhóm/hiển thị "kho công trường" riêng, (2) **khóa sửa/xóa** kho công trường ở trang Quản lý kho (quản lý qua trang Công trường), (3) gán tự động kho khi tạo phiếu theo công trường.

## 3. Frontend flows (dùng dữ liệu có sẵn — không cần API mới)

| Màn hình                       | Hành vi                                                                                                                       |
| ------------------------------ | ----------------------------------------------------------------------------------------------------------------------------- |
| Tạo/Sửa công trường            | Hiển thị `Kho công trường: KHO_CT_RG` (read-only, tự sinh)                                                                    |
| Tạo phiếu nhập mua             | Chọn **công trường đích** (group kho theo site) → `warehouse_id` tự gán kho công trường đó — "NCC giao thẳng" chỉ cần 1 phiếu |
| Tạo phiếu xuất cấp/điều chuyển | Chọn kho đích = kho công trường (từ dropdown, đã gắn nhãn site)                                                               |
| Trang Quản lý kho              | Hiển thị **đủ mọi kho** (kho trung tâm + kho công trường), kho công trường phân biệt bằng badge; không cho sửa/xóa trực tiếp kho công trường                                           |

## 4. Không thay đổi

- `InboundNote` / `OutboundNote` / `StocktakeNote` endpoints — không đổi gì.
- `StockMovement` / tồn kho — giữ nguyên (tồn = SUM sổ kho theo từng kho, kể cả kho công trường).
