# Model — Inbound Note (Phiếu Nhập)

> Django app: `inventory`
> Kế thừa: `models.Model`
> Gồm 2 model: `InboundNote` (phiếu) + `InboundNoteLine` (dòng vật tư)

## 1. Bối cảnh thực tế

Thủ kho (1–2 người, ít tin học) nhập vật tư bằng barcode USB HID (quét mã SKU → tự thêm dòng). Phiếu nhập có 2 loại theo PROJECT_CHARTER F1:

- **Nhập mua** (từ NCC) — có `supplier`, mỗi dòng có đơn giá `unit_price`
- **Nhập hàng công trường trả lại** — không có supplier

Vòng đời phiếu (chốt với user 2026-08-13):

- **Nháp (draft)** — thủ kho đang quét/gõ, chưa ảnh hưởng tồn kho, sửa/xóa thoải mái
- **Đã chốt (posted)** — hệ thống ghi sổ kho (`StockMovement`), tồn tăng. Từ đây phiếu **bất biến**
- **Đã hủy (voided)** — hủy phiếu đã chốt: hệ thống ghi dòng sổ kho ngược dấu, tồn trở về như trước; phiếu vẫn còn trong DB cho kế toán tra

Yêu cầu F5: "giá trị tồn (giá nhập gần nhất)" — giá lưu theo **từng lần nhập thực tế** trên dòng phiếu, không lưu trên Material (D1).

## 2. Model `InboundNote` (phiếu nhập)

| #   | Field        | Kiểu                  | Ràng buộc            | Ghi chú                                    |
| --- | ------------ | --------------------- | -------------------- | ------------------------------------------ |
| 1   | `id`         | BigAutoField (PK)     |                      |                                            |
| 2   | `number`     | CharField(30)         | **unique**           | Số phiếu, auto-generate: `PN-YYYYMMDD-NNN` |
| 3   | `note_type`  | CharField(20) choices | default=`purchase`   | `purchase` / `return_from_site`            |
| 4   | `status`     | CharField(20) choices | default=`draft`      | `draft` / `posted` / `voided` (D5)         |
| 5   | `date`       | DateField             | default=timezone.now | Ngày nghiệp vụ                             |
| 6   | `warehouse`  | FK → `Warehouse`      | PROTECT, required    | Kho nhận hàng                              |
| 7   | `supplier`   | FK → `Supplier`       | PROTECT, null/blank  | Bắt buộc khi `purchase`, null khi `return_from_site` |
| 8   | `created_by` | FK → `iam.User`       | PROTECT, required    | Người lập phiếu (tự set từ request.user)   |
| 9   | `voided_by`  | FK → `iam.User`       | PROTECT, null/blank  | Ai hủy phiếu                               |
| 10  | `voided_at`  | DateTimeField         | null/blank           | Khi nào hủy                                |
| 11  | `void_reason`| TextField             | blank                | Lý do hủy — **bắt buộc khi void**          |
| 12  | `note`       | TextField             | blank                | Ghi chú phiếu                              |
| 13  | `created_at` | DateTimeField         | auto_now_add         |                                            |
| 14  | `updated_at` | DateTimeField         | auto_now             |                                            |

## 3. Model `InboundNoteLine` (dòng vật tư)

| #   | Field          | Kiểu                | Ràng buộc                       | Ghi chú                              |
| --- | -------------- | ------------------- | ------------------------------- | ------------------------------------ |
| 1   | `id`           | BigAutoField (PK)   |                                 |                                      |
| 2   | `inbound_note` | FK → `InboundNote`  | CASCADE, `related_name="lines"` | Phiếu mẹ                             |
| 3   | `material`     | FK → `Material`     | PROTECT                         | Vật tư (chọn bằng SKU/barcode)       |
| 4   | `quantity`     | DecimalField(14, 3) | required, > 0                   | Số lượng (theo đơn vị cơ bản của vật tư) |
| 5   | `unit_price`   | DecimalField(14, 2) | required, >= 0                  | **Đơn giá tại thời điểm nhập** (VND) |
| 6   | `line_no`      | IntegerField        | default=0                       | Thứ tự dòng (set tự động khi tạo)    |
| 7   | `note`         | TextField           | blank                           | Ghi chú dòng                         |
| 8   | `created_at`   | DateTimeField       | auto_now_add                    |                                      |
| 9   | `updated_at`   | DateTimeField       | auto_now                        |                                      |

## 4. Enums / Choices

```python
class BaseNote(models.Model):  # abstract — khung chung của mọi phiếu
    class Status(models.TextChoices):
        DRAFT = "draft", "Nháp"
        POSTED = "posted", "Đã chốt"
        VOIDED = "voided", "Đã hủy"


class InboundNote(BaseNote):
    class Type(models.TextChoices):
        PURCHASE = "purchase", "Mua hàng từ nhà cung cấp"
        RETURN_FROM_SITE = "return_from_site", "Công trường trả lại hàng"
```

## 5. Quan hệ

| Entity đích                        | Cardinality | Mô tả                            | Ghi chú                           |
| ---------------------------------- | ----------- | -------------------------------- | --------------------------------- |
| `InboundNote` → `Warehouse`        | N → 1       | Phiếu thuộc 1 kho                | `warehouse` FK                    |
| `InboundNote` → `Supplier`         | N → 1       | Nhập mua từ NCC                  | `supplier` FK (null khi nhập hàng công trường trả lại) |
| `InboundNote` → `iam.User`         | N → 1       | Người lập phiếu                  | `created_by` FK                   |
| `InboundNoteLine` → `InboundNote`  | N → 1       | Dòng thuộc phiếu                 | `inbound_note` FK, CASCADE        |
| `InboundNoteLine` → `Material`     | N → 1       | Dòng là 1 vật tư                 | `material` FK, PROTECT            |
| `InboundNote` → `StockMovement`    | 1 → N       | Dòng sổ kho sinh ra khi chốt/hủy | Xem [`stock/`](../stock/)         |
| `InboundNote` → `StocktakeNote`    | 1 → N       | Phiếu kiểm kê sau này            | Entity tương lai                  |

## 6. Quyết định thiết kế

| #       | Quyết định                                                             | Lý do                                                                                                                                                                                   |
| ------- | ---------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **D1**  | **Giá lưu trên `InboundNoteLine.unit_price`, không lưu trên Material** | Mỗi NCC có giá khác nhau, giá thay đổi theo thời gian. Lưu theo từng lần nhập thực tế → tự nhiên có lịch sử giá. F5 "giá nhập gần nhất" = query dòng nhập gần nhất của vật tư.          |
| **D2**  | **Không tạo bảng Supplier-Material**                                   | PROJECT_CHARTER F2: "Lịch sử giao dịch: xem các phiếu nhập mua liên quan tới NCC (tự tổng hợp từ F1, không tạo riêng)". NCC nào bán mặt hàng gì, giá bao nhiêu → suy ra từ InboundNote. |
| **D3**  | **`supplier` null khi `note_type=return_from_site`**             | Phiếu nhập hàng công trường trả lại không liên quan NCC. Validate: purchase → bắt buộc supplier, return_from_site → bắt buộc null. |
| **D4**  | **Số phiếu auto-generate `PN-YYYYMMDD-NNN` khi tạo phiếu**             | Thủ kho ít tin học — không để nhập tay. `NNN` = số phiếu trong ngày + 1. Phiếu nháp bị xóa để lại số trống — chấp nhận được (thực tế sổ phiếu vẫn giữ số đã hủy).                        |
| **D5**  | **Vòng đời `draft → posted → voided`** (thay soft delete `is_active`)  | Phiếu nháp chưa đụng tồn → xóa cứng được. Phiếu đã chốt bất biến → hủy bằng cách ghi dòng sổ kho ngược dấu, tồn tự trừ lại, audit trail nguyên vẹn (ADR-0001, stock D2).                |
| **D6**  | **`quantity` decimal_places=3**                                        | Vật tư có thể nhập lẻ (0.5 tấn, 1.25 m³). 3 chữ số thập phân đủ cho xây dựng.                                                                                                           |
| **D7**  | **`line_no` đánh số thứ tự dòng**                                      | Tự set khi tạo (theo thứ tự mảng gửi lên). Giúp frontend hiển thị đúng thứ tự thủ kho quét.                                                                                             |
| **D8**  | **Pagination bật cho list (page_size=20)**                             | Phiếu nhập sẽ nhiều theo thời gian — khác với master data (Warehouse/Supplier không phân trang).                                                                                        |
| **D9**  | **Nested write: tạo phiếu + dòng trong 1 request**                     | Thủ kho quét liên tục — phải gửi 1 request duy nhất chứa phiếu + danh sách dòng. Dùng nested serializer với `transaction.atomic`.                                                       |
| **D10** | **Chốt phiếu = ghi sổ kho (`StockMovement`) trong cùng transaction**   | `POST /{id}/post/`: mỗi dòng sinh 1 dòng sổ kho (+quantity, unit_price nếu purchase, date = date phiếu) + set `status=posted`. Atomic: hoặc ghi hết, hoặc không gì cả.                   |
| **D11** | **Phiếu đã chốt bất biến — không PUT/DELETE**                          | Sửa sai sau khi chốt = hủy phiếu + lập phiếu mới. Giữ lịch sử sạch, tránh lệch sổ kho (user chốt 2026-08-13).                                                                            |
| **D12** | **Hủy phiếu bắt buộc lý do + lưu ai hủy, khi nào**                     | `void_reason` required, set `voided_by`/`voided_at` tự động — đáp ứng NFR "log thao tác quan trọng (xóa phiếu, điều chỉnh tồn)".                                                        |
