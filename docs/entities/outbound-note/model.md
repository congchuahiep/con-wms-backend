# Model — Outbound Note (Phiếu Xuất)

> Django app: `inventory`
> Kế thừa: `BaseNote` (abstract — khung chung + vòng đời, xem [`../inbound-note/model.md`](../inbound-note/model.md))
> Gồm 2 model: `OutboundNote` (phiếu) + `OutboundNoteLine` (dòng vật tư)

## 1. Bối cảnh thực tế

Đối xứng với phiếu nhập: thủ kho xuất vật tư **ra khỏi kho** theo 2 lý do (PROJECT_CHARTER F1):

- **Xuất cấp cho công trường sử dụng** — giao vật tư cho công trường/dự án
- **Điều chuyển kho** — chuyển nội bộ giữa 2 kho của công ty (hàng không rời hệ thống, chỉ đổi chỗ)

Khác biệt với InboundNote:

- **Không có đơn giá** — giá chỉ có nghĩa với nhập mua (stock D5)
- **Chốt phải kiểm tra tồn** — không cho xuất nhiều hơn tồn kho (chặn tồn âm, D4)
- **Điều chuyển sinh 2 dòng sổ kho** cùng lúc: kho đi −, kho đến + (D5)

Vòng đời phiếu: giống InboundNote — `draft → posted → voided`, kế thừa `BaseNote.post()` / `BaseNote.void()`, chỉ viết 2 hook sinh dòng sổ kho.

## 2. Model `OutboundNote` (phiếu xuất)

| # | Field | Kiểu | Ràng buộc | Ghi chú |
|---|---|---|---|---|
| 1 | `id` | BigAutoField (PK) | | Kế thừa `BaseNote` |
| 2 | `number` | CharField(30) | **unique** | `PX-YYYYMMDD-NNN` — sequence riêng cho phiếu xuất |
| 3 | `note_type` | CharField(20) choices | default=`issue_for_use` | `issue_for_use` / `transfer` — xem §3 |
| 4 | `status` | CharField(20) choices | default=`draft` | `BaseNote.Status` — không định nghĩa lại |
| 5 | `date` | DateField | default=today | Ngày xuất (ngày nghiệp vụ) |
| 6 | `warehouse` | FK → `Warehouse` | PROTECT, required | **Kho xuất** |
| 7 | `to_warehouse` | FK → `Warehouse` | PROTECT, null/blank | **Kho đích** — bắt buộc khi `transfer`, null khi `issue_for_use` |
| 8 | `destination` | CharField(100) | blank | Nơi nhận (tên công trường) — bắt buộc khi `issue_for_use`; tương lai: FK → `Site` (xem D3) |
| 9 | `note` | TextField | blank | Ghi chú (kế thừa BaseNote) |
| 10 | `created_by` / `voided_by` / `voided_at` / `void_reason` / `created_at` / `updated_at` | — | | Kế thừa `BaseNote` |

### 2.1 `OutboundNoteLine` (dòng vật tư)

| # | Field | Kiểu | Ràng buộc | Ghi chú |
|---|---|---|---|---|
| 1 | `id` | BigAutoField (PK) | | |
| 2 | `outbound_note` | FK → `OutboundNote` | CASCADE, `related_name="lines"` | Phiếu mẹ |
| 3 | `material` | FK → `Material` | PROTECT | Vật tư |
| 4 | `quantity` | DecimalField(14, 3) | required, > 0 | Số lượng xuất |
| 5 | `line_no` | IntegerField | default=0 | Thứ tự dòng |
| 6 | `note` | TextField | blank | |
| 7 | `created_at` / `updated_at` | | | |

> **Không có `unit_price`** — nhất quán stock D5: giá chỉ lưu cho dòng nhập mua.

## 3. Enums / Choices

```python
class OutboundNote(BaseNote):
    class Type(models.TextChoices):
        ISSUE_FOR_USE = "issue_for_use", "Xuất cấp cho công trường sử dụng"
        TRANSFER = "transfer", "Điều chuyển kho"
```

`status` dùng `BaseNote.Status` (`draft` / `posted` / `voided`).

## 4. Quan hệ

| Entity đích | Cardinality | Mô tả |
|---|---|---|
| `OutboundNote` → `Warehouse` | N → 1 | Kho xuất (`warehouse`) |
| `OutboundNote` → `Warehouse` | N → 1 | Kho đích khi điều chuyển (`to_warehouse`) |
| `OutboundNote` → `iam.User` | N → 1 | Người lập phiếu |
| `OutboundNoteLine` → `OutboundNote` | N → 1 | Dòng thuộc phiếu, CASCADE |
| `OutboundNoteLine` → `Material` | N → 1 | Dòng là 1 vật tư |
| `OutboundNote` → `StockMovement` | 1 → N | Sinh ra khi chốt/hủy: 1 dòng/dòng phiếu (xuất cấp) hoặc 2 dòng/dòng phiếu (điều chuyển) |

## 5. Luật chốt phiếu — hook `_build_post_movements`

1. **Kiểm tra tồn** cho từng dòng: `SUM(quantity)` các dòng sổ kho của `(warehouse, material)` ≥ `line.quantity`. Thiếu → `ValidationError` 400 kèm mã vật tư. **Không cho phép tồn âm** (D4).
2. `issue_for_use` → mỗi dòng sinh 1 dòng sổ kho:
   - `movement_type = outbound_issue_for_use`, `quantity = −line.quantity`, `warehouse = phiếu.warehouse`, `outbound_note = phiếu`, `unit_price = None`
3. `transfer` → mỗi dòng sinh **2** dòng sổ kho (cùng `outbound_note`, cùng `date`):
   - Kho đi: `outbound_transfer_to_warehouse`, `quantity = −line.quantity`, `warehouse = phiếu.warehouse`
   - Kho đến: `inbound_transfer_from_warehouse`, `quantity = +line.quantity`, `warehouse = phiếu.to_warehouse`

Toàn bộ trong `transaction.atomic` (đã có sẵn ở `BaseNote.post()`).

## 6. Luật hủy phiếu — hook `_build_void_movements`

Giống InboundNote: với mỗi dòng sổ kho gốc của phiếu (phiếu điều chuyển có 2 dòng/dòng phiếu → đảo cả 2) → ghi 1 dòng ngược dấu (`quantity = −gốc`, `reversal_of = gốc`, `reason`, `date = hôm nay`). Tồn kho cả 2 đầu tự trở về như trước.

## 7. Quyết định thiết kế

| # | Quyết định | Lý do |
|---|---|---|
| **D1** | **Không có `unit_price` trên dòng xuất** | Nhất quán stock D5 — giá chỉ lưu cho nhập mua, nuôi "giá nhập gần nhất". Dòng xuất không mang giá. |
| **D2** | **`to_warehouse` trên phiếu, không trên dòng — 1 phiếu = 1 kho đích** | User chốt 2026-08-18: "1 phiếu = 1 kho đích". Thủ kho ít tin học — 1 phiếu điều chuyển = 1 kho nhận. Chuyển nhiều kho → lập nhiều phiếu. |
| **D3** | **`destination` free text, thiết kế sẵn để sau đổi thành FK → `Site`** | Dự án **có** báo cáo công trường và sẽ có model "Công trường" (Site) trong tương lai (user xác nhận 2026-08-18). Giai đoạn này chưa tạo Site (YAGNI) — để `destination` CharField; khi có Site entity chỉ đổi thành FK nullable, không phá data. |
| **D4** | **Chặn cứng tồn âm khi chốt phiếu xuất** | User chốt 2026-08-18: "làm gì có việc xuất hàng từ kho mà hàng âm". Không đủ tồn → 400, không chốt. |
| **D5** | **Điều chuyển = 1 phiếu → 2 dòng sổ kho cùng lúc** | Chứng từ là 1 (thủ kho lập 1 phiếu), nhưng sổ kho phải ghi 2 đầu (kho đi −, kho đến +). `MovementType` trên dòng sổ phân biệt đầu đi/đến — đúng kiến trúc "chứng từ ≠ dòng sổ kho" (stock model.md §3). |
| **D6** | **Số phiếu auto-generate `PX-YYYYMMDD-NNN`** | Giống InboundNote D4 — thủ kho không gõ tay, `NNN` = sequence trong ngày của riêng phiếu xuất. |
