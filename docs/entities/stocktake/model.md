# Model — Stocktake Note (Phiếu Kiểm Kê)

> Django app: `inventory` (user chốt: gộp vào `inventory`, không tách app `stocktake`)
> Kế thừa: `BaseNote` (abstract — khung chung + vòng đời, xem [`../inbound-note/model.md`](../inbound-note/model.md))
> Gồm 2 model: `StocktakeNote` (phiếu) + `StocktakeLine` (dòng vật tư)

## 1. Bối cảnh thực tế — kiểm kê là gì?

**Kiểm kê = đi đếm hàng thực tế trong kho rồi đối chiếu với sổ sách.**

Thủ kho đếm thực tế và so với số hệ thống đang ghi (lấy từ `/api/stock/`), biết được **chênh lệch** của từng vật tư:

- Sổ ghi 100 bao xi măng, đếm thực tế 97 → **chênh lệch −3** (thiếu, kèm lý do: hư/mất/rách)
- Sổ ghi 0 bao đường, thực tế phát hiện 1 bao → **chênh lệch +1** (thừa)

Khi chốt phiếu, hệ thống điều chỉnh tồn theo đúng chênh lệch từng dòng để **sổ khớp với thực tế**.

**Quyết định quan trọng (user chốt 2026-08-18):** phiếu kiểm kê **chỉ chứa chênh lệch (`difference`) + lý do** — KHÔNG lưu "số trên sổ" (`book_quantity`) hay "số đếm được" (`counted_quantity`). Xem D1/D2.

Quy trình thực tế của thủ kho:

1. Mở màn hình kiểm kê cho kho X → client tự fetch `/api/stock/?warehouse=X` để hiển thị tồn hiện tại làm bảng đối chiếu (số này **động**, không lưu).
2. Ra kho đếm thực tế, nhập số đếm (hoặc nhập thẳng chênh lệch) cho từng vật tư bị lệch + lý do.
3. Tạo phiếu kiểm kê với các dòng chênh lệch — trạng thái **nháp**, có thể sửa trước khi chốt.
4. **Chốt**: hệ thống ghi dòng điều chỉnh tồn cho từng dòng chênh lệch. Phiếu bất biến từ đây.
5. Chốt nhầm → **hủy**: ghi dòng ngược dấu, tồn trở về như trước. Muốn sửa thì làm lại phiếu mới.

## 2. Model `StocktakeNote` (phiếu kiểm kê)

| # | Field | Kiểu | Ràng buộc | Ghi chú |
|---|---|---|---|---|
| 1 | `id` | BigAutoField (PK) | | Kế thừa `BaseNote` |
| 2 | `number` | CharField(30) | **unique** | `PK-YYYYMMDD-NNN` — sequence riêng cho phiếu kiểm kê |
| 3 | `status` | CharField(20) choices | default=`draft` | `BaseNote.Status` |
| 4 | `date` | DateField | default=today | Ngày kiểm kê |
| 5 | `warehouse` | FK → `Warehouse` | PROTECT, required | Kho được kiểm kê |
| 6 | `note` | TextField | blank | Ghi chú |
| 7 | `created_by` / `voided_by` / `voided_at` / `void_reason` / `created_at` / `updated_at` | — | | Kế thừa `BaseNote` |

> **Không có `note_type`** — phiếu kiểm kê chỉ có 1 loại.

### 2.1 `StocktakeLine` (dòng vật tư điều chỉnh)

| # | Field | Kiểu | Ràng buộc | Ghi chú |
|---|---|---|---|---|
| 1 | `id` | BigAutoField (PK) | | |
| 2 | `stocktake_note` | FK → `StocktakeNote` | CASCADE, `related_name="lines"` | Phiếu mẹ |
| 3 | `material` | FK → `Material` | PROTECT | Vật tư bị chênh lệch |
| 4 | `difference` | DecimalField(14, 3) | required, ≠ 0 | **Chênh lệch có dấu**: âm = thiếu (sổ > thực tế), dương = thừa (thực tế > sổ). Không lưu dòng lệch 0 |
| 5 | `reason` | TextField | blank | Lý do — **bắt buộc khi `difference ≠ 0`** (hư/mất/sai số/thừa) — validate lúc chốt |
| 6 | `line_no` | IntegerField | default=0 | Thứ tự dòng |
| 7 | `note` | TextField | blank | |
| 8 | `created_at` / `updated_at` | | | |

## 3. Enums / Choices

Không có enum riêng — `status` dùng `BaseNote.Status` (`draft` / `posted` / `voided`). Loại dòng sổ kho sinh ra dùng `StockMovement.Type.STOCKTAKE_ADJUSTMENT`.

## 4. Quan hệ

| Entity đích | Cardinality | Mô tả |
|---|---|---|
| `StocktakeNote` → `Warehouse` | N → 1 | Kho được kiểm kê |
| `StocktakeNote` → `iam.User` | N → 1 | Người lập phiếu |
| `StocktakeLine` → `StocktakeNote` | N → 1 | Dòng thuộc phiếu, CASCADE |
| `StocktakeLine` → `Material` | N → 1 | Dòng là 1 vật tư |
| `StocktakeNote` → `StockMovement` | 1 → N | Dòng điều chỉnh sinh ra khi chốt — 1 dòng cho mỗi dòng phiếu |

## 5. Luật lập phiếu (tạo dòng)

**Client gửi thẳng các dòng chênh lệch** ngay khi tạo phiếu:

```json
{
    "date": "2026-08-18",
    "warehouseId": 1,
    "lines": [ { "materialId": 1, "difference": "-3", "reason": "3 bao rách vỡ" } ]
}
```

- Hệ thống **không tự sinh dòng** — việc hiển thị "kho có những gì" để thủ kho đối chiếu là của client (fetch `/api/stock/?warehouse=X`, xem D2)
- `difference` **≠ 0** cho mọi dòng; `reason` phải kèm
- Phiếu còn **nháp**: sửa/xóa dòng thoải mái (replace-all khi PUT, giống các phiếu khác)

## 6. Luật chốt phiếu — hook `_build_post_movements`

Với từng dòng:

1. **Kiểm tra tồn (server tính lại lúc chốt):** `difference ≥ −tồn_hiện_tại` (tồn hiện tại = `SUM(quantity)` sổ kho của `(warehouse, material)` **tại thời điểm chốt**, không phải lúc tạo phiếu). Không đạt → `ValidationError` 400 (bắt nhầm dấu/số, chặn tồn âm — D4).
2. **Kiểm tra lý do:** `difference ≠ 0` mà thiếu `reason` → 400.
3. Sinh 1 dòng sổ kho:
   - `movement_type = stocktake_adjustment`
   - `quantity = difference` (âm nếu thiếu, dương nếu thừa)
   - `unit_price = None`, `date = phiếu.date`, `stocktake_note = phiếu`, `reason = line.reason`, `warehouse = phiếu.warehouse`

Toàn bộ trong `transaction.atomic` (có sẵn ở `BaseNote.post()`).

## 7. Luật hủy phiếu — hook `_build_void_movements`

Giống các phiếu khác: với mỗi dòng sổ kho gốc của phiếu → ghi 1 dòng ngược dấu (`reversal_of`, `reason`). Tồn kho trở về giá trị sổ **trước khi kiểm kê** (muốn sửa lại thì lập phiếu mới).

> Phiếu chốt không có dòng nào (không thể — mọi dòng đều `difference ≠ 0`)... trường hợp đặc biệt: phiếu nháp không dòng → chốt báo lỗi "phiếu phải có ít nhất 1 dòng".

## 8. Quyết định thiết kế

| # | Quyết định | Lý do |
|---|---|---|
| **D1** | **KHÔNG lưu `book_quantity` / `counted_quantity` — chỉ lưu `difference` + `reason`** | User chốt 2026-08-18. Snapshot "số trên sổ" lưu vào DB sẽ **cũ đi khi kho biến động** (người khác chốt nhập/xuất giữa chừng) — lưu một con số không còn đúng gây hiểu nhầm audit, và luồng "tạo → sửa từng dòng" rườm rà. Chỉ cần chênh lệch là đủ để ghi sổ. |
| **D2** | **Tồn hiện tại để đối chiếu là số ĐỘNG — client tự fetch `/api/stock/`, hệ thống không lưu** | Bảng đối chiếu "sổ vs đếm" là việc của UI: client lấy tồn tươi tại thời điểm nhập. Không tự sinh dòng cho mọi vật tư — phiếu chỉ chứa các điều chỉnh thật. |
| **D3** | **`reason` bắt buộc khi `difference ≠ 0`** | NFR "log thao tác quan trọng": kế toán cần biết vì sao có chênh lệch (hư/mất/sai số/thừa). |
| **D4** | **Chốt phiếu: `difference ≥ −tồn_hiện_tại` (server tính lại tại lúc chốt)** | Chặn tồn âm và bắt nhầm dấu/số (nhập `-150` khi kho chỉ có 100). Tồn tính tại thời điểm chốt — không phụ thuộc snapshot nào. |
| **D5** | **Audit tái dựng được mà không cần lưu "số trên sổ"** | "Sổ trước điều chỉnh" = `SUM(quantity)` các dòng sổ kho trước dòng `stocktake_adjustment` này — sổ kho là nguồn sự thật (ADR-0001), không cần chép vào phiếu. |
| **D6** | **Hủy phiếu kiểm kê = đảo dấu các dòng điều chỉnh** | Nhất quán stock D2: dòng sổ kho bất biến, mọi sửa sai đều là ghi ngược dấu. |
| **D7** | **App `inventory` — không tách app `stocktake`** | User chốt 2026-08-18: gộp chung với Inbound/Outbound/StockMovement — 3 phiếu cùng vòng đời, cùng 1 FK nguồn trong sổ kho. |
| **D8** | **Không có `note_type`** | Chỉ 1 loại phiếu kiểm kê — YAGNI. |