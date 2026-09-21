# Model — Site Material Requirement (Định mức vật tư công trường)

> Django app: `sites` (model mới) + `inventory` (guard chặn phiếu) + `warehouse` (đóng kho khi tất toán)
> Kế thừa: `models.Model`

## 1. Bối cảnh thực tế

Mỗi công trường có đúng 1 kho công trường (`Warehouse.site` 1–1, tự tạo qua signal — xem [`../site-warehouse/`](../site-warehouse/README.md)). Toàn bộ lịch sử nhập/xuất của kho nằm trong sổ kho `StockMovement`; **tồn kho = SUM dòng sổ kho** theo `(warehouse, material)`.

Vấn đề: hệ thống chưa mô tả được **công trường cần những vật tư gì, số lượng bao nhiêu**. Yêu cầu (user chốt 2026-09-20):

1. Công trường khai báo **định mức vật tư** (vd: 3 bao xi măng, 20000 viên gạch) — chỉnh sửa nhanh, dùng làm **mốc so sánh** với tồn kho công trường.
2. Định mức **không giới hạn** nhập thêm vật tư ngoài định mức (máy khoan, máy xúc... vẫn về kho công trường bình thường).
3. UI so sánh: `3/3 bao xi măng: đủ`, `10000/20000 viên gạch: thiếu`.
4. **Không có khái niệm "công trường đã dùng"** — không tồn tại thao tác làm trừ tồn kho công trường vì mục đích sử dụng; định mức chỉ là mốc so sánh với số dư sổ kho.
5. Khi công trường **đủ mọi định mức** và hoàn thành → người dùng **Tất toán**: vật tư thừa (phần vượt định mức) + vật tư không thuộc định mức được chuyển về một **kho khác còn hoạt động**; mặc định hệ thống tính trước số lượng, người dùng có thể chỉnh từng dòng.

## 2. Thay đổi model

### 2.1 `Site` — thay `is_active` (bool) bằng `status` (enum)

| #   | Field        | Kiểu Kiểu          | Ràng buộc                                | Ghi chú                                                                   |
| --- | ------------ | --------------------- | ------------------------------------ | ------------------------------------------------------------------------- |
| 1   | `status`     | CharField(20) choices | default=`active`, thay `is_active`    | Xem enum §3.1 — migration dữ liệu `is_active` → `status`                  |
| 2   | `settled_at` | DateTimeField         | null/blank                           | Thời điểm tất toán (mới, chỉ có khi `status=completed`)                   |
| 3   | `settled_by` | FK → `iam.User`       | PROTECT, null/blank                  | Người thực hiện tất toán (mới)                                            |

> **Không giữ `is_active`** — user chốt "phải dùng trạng thái enum cho đúng đắn, `is_active` có rất nhiều trường hợp xảy ra". Migration chuyển dữ liệu: `is_active=True → active`, `is_active=False → inactive`; xóa cột cũ.

### 2.2 Model mới `SiteMaterialRequirement` (bảng định mức)

| #   | Field     | Kiểu               | Ràng buộc                                                          | Ghi chú                                                          |
| --- | --------- | ------------------ | ------------------------------------------------------------------ | ---------------------------------------------------------------- |
| 1   | `id`      | BigAutoField (PK)  |                                                                    |                                                                  |
| 2   | `site`    | FK → `sites.Site`  | PROTECT, `related_name="material_requirements"`                    | Công trường sở hữu định mức                                      |
| 3   | `material`| FK → `catalog.Material` | PROTECT, `related_name="site_material_requirements"`           | Vật tư                                                            |
| 4   | `quantity`| DecimalField(14,3) | required, **> 0** (CheckConstraint `ck_smr_quantity_positive`)     | Số lượng định mức — theo đơn vị của vật tư (D3)                  |
| 5   | `note`    | TextField          | blank                                                              | Ghi chú dòng (vd: "cho các cọc móng đợt 2")                     |
| 6   | `created_at` / `updated_at` | DateTimeField | auto_now_add / auto_now                              |                                                                  |

- `db_table = "site_material_requirement"`
- **UniqueConstraint `(site, material)`** — 1 vật tư chỉ có 1 dòng định mức/công trường (`uq_smr_site_material`).
- `ordering = ["id"]`; serializer trả theo mã vật tư.

> Không lưu trường `unit` — đơn vị lấy từ `Material.unit` (D3, user chốt câu 6: "chọn đơn vị định mức của một vật tư có sẵn").

### 2.3 `Warehouse` — không thêm field

Khi tất toán: `warehouse.is_active = False` (đóng kho công trường). Kho dùng `is_active` sẵn có — không cần thêm trạng thái riêng (D8).

## 3. Enums / Choices

### 3.1 `Site.Status`

```python
class Status(models.TextChoices):
    ACTIVE = "active", "Đang hoạt động"
    COMPLETED = "completed", "Đã hoàn thành"
    INACTIVE = "inactive", "Ngừng hoạt động"
```

| Trạng thái   | Ý nghĩa                                                            | Chuyển vào bằng cách nào                       |
| ------------ | ------------------------------------------------------------------ | ---------------------------------------------- |
| `active`     | Đang thi công, có thể nhập/xuất/kiểm kê, sửa định mức, tất toán    | Tạo mới / mặc định                             |
| `completed`  | Đã đủ định mức + tất toán xong                                     | Chỉ qua **Tất toán** (service)                 |
| `inactive`   | Ngừng hoạt động (thay `is_active=False` cũ)                        | `DELETE /api/sites/{id}/` (soft-delete)        |

### 3.2 Trạng thái so sánh dòng (computed, không lưu)

| Giá trị         | Điều kiện                                             | Hiển thị                  |
| --------------- | ----------------------------------------------------- | ------------------------- |
| `sufficient`    | có định mức và `tồn >= định mức`                      | "Đủ" (xanh)               |
| `insufficient`  | có định mức và `tồn < định mức`                       | "Thiếu" (đỏ/cam)          |
| `not_in_plan`   | không có định mức, tồn > 0 (vật tư dùng máy móc...)   | "Ngoài định mức" (xám)    |

## 4. Luồng nghiệp vụ

### 4.1 So sánh định mức vs tồn kho

- Tồn kho công trường = `SUM(quantity)` các dòng `StockMovement` theo `(warehouse=site.warehouse, material)` — giống `StockBalanceViewSet` hiện có (stock D1: sổ kho là nguồn sự thật, không có bảng tồn).
- Bảng so sánh = **hợp** của (a) mọi dòng định mức + (b) mọi vật tư có tồn > 0 trong kho công trường.
- Số "thiếu/đủ" hiển thị: `min(tồn, định mức)/định mức` · kèm trạng thái.
- **Không có bất kỳ thao tác nào làm trừ tồn kho công trường theo định mức** (không có khái niệm "đã dùng").

### 4.2 Tất toán (settlement)

```
Điều kiện mở  : site.status == active  VÀ  mọi dòng định mức có tồn >= định mức  (kiểm tra cứng tại thời điểm thực thi)
Thao tác      : chọn kho đích (active, khác kho công trường) + danh sách dòng trả về
Mặc định dòng :  - vật tư trong định mức  → max(tồn − định mức, 0)   ("định mức coi như đã dùng")
                  - vật tư ngoài định mức → toàn bộ tồn
                  - người dùng chỉnh được từng dòng trong khoảng [0, tồn]
Kết quả       : 1 phiếu OutboundNote(transfer, warehouse=kho CT, to_warehouse=kho đích) → chốt ngay
                 → site.status=completed, settled_at, settled_by
                 → warehouse.is_active=False (đóng kho)
                 toàn bộ trong transaction.atomic
Lý do giảm số lượng : mỗi dòng trả về có thể kèm `note` — bắt buộc người dùng ghi lý do khi
                 chọn **ít hơn** giá trị mặc định (user chốt bổ sung 2026-09-20); lưu vào `OutboundNoteLine.note`
```

- Phiếu tất toán tận dụng **toàn bộ luồng điều chuyển sẵn có**: kiểm tra tồn khi chốt (chặn xuất > tồn), sinh 2 dòng sổ kho (`outbound_transfer_to_warehouse` −, `inbound_transfer_from_warehouse` +), có `number` `PX-YYYYMMDD-NNN`, `created_by`.
- Ghi chú phiếu: `"Tất toán công trường <code> — <tên>"`.
- Sau tất toán: **chặn mọi phiếu mới** (nhập/xuất/kiểm kê) dính đến kho công trường đã đóng (D8); tất toán **không hủy được** (D9).

## 5. Quan hệ

| Entity đích                          | Cardinality | Mô tả                                           |
| ------------------------------------ | ----------- | ----------------------------------------------- |
| `Site` → `SiteMaterialRequirement`   | 1 → N       | 1 công trường có N dòng định mức (unique theo vật tư) |
| `SiteMaterialRequirement` → `Site`   | N → 1       | PROTECT                                         |
| `SiteMaterialRequirement` → `Material` | N → 1     | PROTECT                                         |
| `Site` → `Warehouse`                 | 1 ↔ 1       | Giữ nguyên (site-warehouse)                      |
| `Site` → `OutboundNote` (tất toán)   | 1 → 1..N    | Phiếu điều chuyển do settlement tạo, `warehouse.site = site` |

## 6. Quyết định thiết kế

| #    | Quyết định                                                                                                           | Lý do                                                                                                                                                                                                                     |
| ---- | -------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **D1** | **Không tạo khái niệm "đã sử dụng"** — định mức chỉ là mốc so sánh với tồn sổ kho                                    | User chốt (câu 1): mọi vật tư vào kho công trường là để dùng; định mức là mốc "sẽ/đã dùng", không có thao tác trừ tồn theo mức sử dụng. Tồn kho vẫn do sổ kho sinh ra (nhập + / điều chuyển −).                         |
| **D2** | **Bảng con `SiteMaterialRequirement`** thay vì JSONField trên `Site`                                                 | Query/tổng hợp/validate/unique theo vật tư được; đủ nhỏ (vài chục dòng/công trường); đồng nhất pattern `InboundNoteLine`/`OutboundNoteLine`.                                                                              |
| **D3** | **Không lưu `unit`** — đơn vị lấy từ `Material.unit`                                                                 | User chốt (câu 6). Vật tư có đúng 1 đơn vị (`Material.unit`); lưu thêm unit dư thừa + có thể lệch.                                                                                                                       |
| **D4** | **`Site.status` enum (active/completed/inactive) thay `is_active`**                                                   | User chốt (câu 3): `is_active` bool không diễn tả được trạng thái "đã hoàn thành". Migration dữ liệu một lần, giữ soft-delete qua `inactive`.                                                                             |
| **D5** | **Tất toán = 1 `OutboundNote(transfer)` chốt ngay + đổi trạng thái, trong 1 transaction**                             | Tận dụng 100% luồng điều chuyển sẵn có (kiểm tra tồn, sổ kho ±, số phiếu, audit `created_by`) — không viết lại logic ghi sổ. Settlement là hành động đóng, không phải chứng từ nháp.                                     |
| **D6** | **Mặc định số lượng trả về: định mức → `max(tồn−định mức, 0)`; ngoài định mức → toàn bộ tồn; người dùng chỉnh [0, tồn]** | User chốt (câu 2): hệ thống tính trước "phần thừa/ngoài định mức", nhưng vẫn cho phép điều chỉnh từng dòng (chọn bớt dòng/giảm số). Định mức được coi là phần "công trường đã dùng" nên ở lại. **Bổ sung: khi trả ÍT HƠN mặc định phải ghi lý do (`note` dòng) — lưu vào `OutboundNoteLine.note`**. |
| **D7** | **Chặn cứng tất toán khi chưa đủ mọi định mức**                                                                       | User chốt (câu 4): chỉ tất toán khi công trường đã được cấp đủ. Kiểm tra tại thời điểm thực thi (balance tính từ sổ kho) — tránh race cũng như dữ liệu lệch do phiếu phát sinh giữa lúc mở dialog và lúc xác nhận.          |
| **D8** | **Guard chặn phiếu vào kho đã đóng: `BaseNote.post()`/`void()` + validate serializer khi tạo**                        | Kho đóng = `warehouse.is_active=False` hoặc thuộc site `status != active`. Chặn ở chốt (backstop, cover cả nháp tạo trước khi đóng) + chặn sớm khi tạo/sửa phiếu (UX), kể cả `to_warehouse` khi điều chuyển.             |
| **D9** | **Tất toán không thể hủy/phản chuyển (phiếu tất toán cùng các phiếu trên kho đóng bị chặn void)**                     | Điểm kết thúc rõ ràng cho số kế toán. Nếu nhập sai → phải mở lại công trường thủ công (backlog §7).                                                                                                                       |
| **D10** | **Bảng so sánh tính từ sổ kho (aggregate), không cache**                                                              | Nhất quán ADR-0001 / stock D1; quy mô nhỏ, aggregate trong ms. Bao gồm cả vật tư ngoài định mức có tồn > 0 để bảng phản ánh "kho thực tế có gì".                                                                           |

## 7. Backlog (tương lai)

| Mục                               | Ghi chú                                                                                    |
| --------------------------------- | ------------------------------------------------------------------------------------------ |
| Mở lại công trường đã tất toán    | Action admin/service để sửa sai (đảo trạng thái + mở kho)                                  |
| Phân quyền thủ kho tất toán       | Hiện write = `IsAdmin`; nếu cần thủ kho tự tất toán → permission riêng (auth.md)           |
| Cảnh báo định mức sắp thiếu       | Tương tự `StockAlert` backlog (stock model.md) — gộp khi làm                              |