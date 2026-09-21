# Model — Site Warehouse (Kho Công Trường)

> Django app: `warehouse` (thêm field) + `sites` (auto-create qua signal)
> Thay đổi: `Warehouse` thêm `site` OneToOneField — **không tạo bảng mới, không đổi model `inventory`**

## 1. Bối cảnh thực tế

Công trường xây dựng có **kho/bãi vật tư tại chỗ** (do người nhận hàng — field `Site.manager` — quản lý). Hai dòng hàng thật:

```
Dòng 1 (phổ biến):  NCC ──→ Kho công trường ──→ thi công (tiêu hao)
Dòng 2:             NCC ──→ Kho chính ──→ điều chuyển ──→ Công trường
```

Model cũ chỉ hỗ trợ dòng 2 → buộc khai 2 phiếu giả (nhập kho chính dù hàng không qua) khi NCC giao thẳng. Giải pháp: cho mỗi `Site` một `Warehouse` liên kết (kho công trường) — mọi luồng phiếu hiện có dùng nguyên vẹn.

## 2. Thay đổi model

### 2.1 `Warehouse` — thêm field `site`

| #   | Field  | Kiểu                           | Ràng buộc                                                            | Ghi chú                                                                          |
| --- | ------ | ------------------------------ | -------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| 1   | `site` | `OneToOneField` → `sites.Site` | `null=True, blank=True, on_delete=PROTECT, related_name="warehouse"` | Kho công trường: `site` = công trường sở hữu; kho thường (KHO_CHINH...) = `null` |

- `OneToOneField` → mỗi site tối đa 1 kho; signal đảm bảo tạo ngay khi tạo site → chính xác **1 kho / 1 công trường**.
- `on_delete=PROTECT` — đồng nhất convention repo (không xóa cứng đối tượng đang được tham chiếu; Site vốn soft-delete `is_active`).
- Không thêm field vị trí nào (YAGNI — đồng nhất `warehouse/model.md` D1: kho = bãi chứa phẳng, không Location).

### 2.2 Tự động tạo kho công trường

Khi tạo `Site` mới (`Site.objects.create(...)` — qua API/admin/shell/seed), signal `post_save` trong `sites/apps.py` tạo kho ngay trong cùng luồng:

```python
def ensure_site_warehouse(sender, instance, created, **kwargs):
    if not created:
        return  # chỉ tạo khi mới tạo Site, không khi update
    code = "KHO_" + instance.code  # cắt ≤ 20 ký tự (Warehouse.code max_length=20)
    Warehouse.objects.update_or_create(
        code=code,
        defaults={"name": instance.name, "site": instance},  # tên = tên công trường
    )
```

- `update_or_create` theo `code` (`KHO_<SITE_CODE>`): chạy lại idempotent, và nếu code bị trùng với kho do ai đó tự tạo trước thì kho đó trở thành kho công trường (edge hiếm, chấp nhận).
- Cắt độ dài: `warehouse_code_for_site(site)` helper → `("KHO_" + site.code)[:20]`.

### 2.3 Luồng phiếu (inventory — KHÔNG đổi model, chỉ đổi quy ước dữ liệu)

| Nghiệp vụ                               | Phiếu                              | Dữ liệu                                                                                             |
| --------------------------------------- | ---------------------------------- | --------------------------------------------------------------------------------------------------- |
| **Mua NCC giao thẳng CT**               | `InboundNote` (`purchase`)         | `warehouse` = kho công trường, `supplier` bắt buộc, `site` = null (site suy ra từ `warehouse.site`) |
| Xuất kho chính → CT                     | `OutboundNote` (`transfer`)        | `warehouse` = kho chính, `to_warehouse` = kho công trường                                           |
| Xuất dùng tại CT (trừ tồn khi thi công) | `OutboundNote` (`issue_for_use`)   | `warehouse` = kho công trường, `site` = chính công trường đó                                        |
| Trả hàng từ CT về kho                   | `InboundNote` (`return_from_site`) | như hiện tại                                                                                        |
| Kiểm kê kho công trường                 | `StocktakeNote`                    | `warehouse` = kho công trường                                                                       |

→ Tồn kho công trường = `SUM(StockMovement)` của kho đó (đã nhập +, xuất dùng −) — đáp ứng "theo dõi số lượng vật tư đã nhập là chính".

#### Validation bổ sung (nhẹ, khuyến nghị)

- **`issue_for_use`**: nếu `warehouse.site` không null (kho công trường) → bắt buộc `site == warehouse.site` ("kho công trường chỉ xuất dùng cho chính công trường của nó").
- **`purchase` vào kho công trường**: cho phép (hiện đang cho phép, `purchase` chỉ chặn `site` FK — giữ nguyên).

## 3. Quan hệ (cập nhật)

| Entity đích                             | Cardinality                           | Mô tả                                                    |
| --------------------------------------- | ------------------------------------- | -------------------------------------------------------- |
| `Site` ↔ `Warehouse`                    | **1 ↔ 0..1** (thực tế 1–1 sau signal) | `Warehouse.site` OneToOneField, reverse `site.warehouse` |
| `Site` → `InboundNote` / `OutboundNote` | 1 → N                                 | giữ nguyên (site FK hiện có)                             |

## 4. Quyết định thiết kế

| #      | Quyết định                                                                             | Lý do                                                                                                                            |
| ------ | -------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| **D1** | Thêm `Warehouse.site` OneToOneField (null) thay vì `Site.warehouse` FK                 | 1 kho = 1 công trường; kho thường giữ `null`; báo cáo tồn chạy nguyên vẹn theo kho                                               |
| **D2** | Auto-create qua **signal `post_save`** trên `Site` (app `sites`), không qua serializer | Áp dụng cho **mọi** đường tạo Site (API/admin/shell/seed) — đúng semantics "công trường có kho tự nhiên"                         |
| **D3** | Code kho = `KHO_<SITE_CODE>` (cắt 20 ký tự)                                            | Nhất quán quy ước code repo (`KHO_CHINH`, `CT_RG`...); dễ nhớ, dễ seed                                                           |
| **D4** | `on_delete=PROTECT`                                                                    | Site soft-delete, không xóa cứng — không xung đột; đồng nhất repo                                                                |
| **D5** | **Không đổi model inventory** — chỉ đổi quy ước dữ liệu + thêm validation nhẹ          | InboundNote/OutboundNote/StockMovement vốn đã generic theo `warehouse`; tận dụng 100% code + sổ kho hiện có, giảm rủi ro migrate |
| **D6** | Validation: kho công trường chỉ `issue_for_use` cho chính site của nó                  | Chống dữ liệu lệch (xuất kho CT_RG cho CT_ND) — rẻ, an toàn                                                                      |
| **D7** | Công trường track "đã nhập" là chính; xuất dùng tại CT là tùy chọn                     | User chốt: quản lý nhỏ chỉ cần biết nhập về CT bao nhiêu; không ép luồng tiêu hao phức tạp                                       |
