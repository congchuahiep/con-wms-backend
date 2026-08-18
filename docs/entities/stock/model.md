# Model — Stock (Sổ kho & Tồn kho)

> Django app: `inventory`
> Kế thừa: `models.Model`
> Gồm **1 model duy nhất**: `StockMovement` (dòng sổ kho).
> **Không có bảng tồn kho** — tồn là con số tính ra từ sổ kho (xem D1, ADR-0001).

## 1. Bối cảnh thực tế

Thủ kho nhập/xuất hàng ngày qua các phiếu. Câu hỏi nghiệp vụ quan trọng nhất: **"tồn kho sinh ra như thế nào và có sửa tay được không?"**

Câu trả lời thiết kế (đã chốt với user, 2026-08-13):

- Mọi thay đổi hàng trong kho **phải đi qua một phiếu** (nhập / xuất / kiểm kê) — không ai được tự ý cộng trừ tồn.
- Khi phiếu được **chốt**, mỗi dòng phiếu sinh ra 1+ dòng **sổ kho** (StockMovement): nhập = +số lượng, xuất = −số lượng.
- Tồn kho hiện tại = **tổng các dòng sổ kho** — giống "số dư ngân hàng" được cộng trừ từ các giao dịch, không ai sửa tay con số dư.
- Phiếu chốt rồi **không sửa được**; muốn hủy → ghi các dòng sổ kho **ngược dấu** (reversal), tồn tự trở về như trước.

## 2. Model `StockMovement` (dòng sổ kho)

| #   | Field            | Kiểu                       | Ràng buộc           | Ghi chú                                                                     |
| --- | ---------------- | -------------------------- | ------------------- | --------------------------------------------------------------------------- |
| 1   | `id`             | BigAutoField (PK)          |                     |                                                                             |
| 2   | `material`       | FK → `catalog.Material`    | PROTECT, required   | Vật tư                                                                      |
| 3   | `warehouse`      | FK → `warehouse.Warehouse` | PROTECT, required   | Kho — **không có Location** (Warehouse D1: kho là bãi chứa)                 |
| 4   | `quantity`       | DecimalField(14, 3)        | required            | **Có dấu**: nhập **+**, xuất **−**                                          |
| 5   | `unit_price`     | DecimalField(14, 2)        | null/blank          | Chỉ có khi `movement_type=inbound_purchase_from_supplier` — nuôi "giá nhập gần nhất" (F5) |
| 6   | `movement_type`  | CharField(40) choices      | required            | 6 loại — xem §3                                                             |
| 7   | `date`           | DateField                  | required            | **Ngày nghiệp vụ** — copy từ phiếu, dùng cho báo cáo kỳ (xem D6)            |
| 8   | `inbound_note`   | FK → `InboundNote`         | PROTECT, null/blank | Phase 1 — xem D7                                                            |
| 9   | `outbound_note`  | FK → `OutboundNote`        | PROTECT, null/blank | Future (entity chưa thiết kế)                                               |
| 10  | `stocktake_note` | FK → `StocktakeNote`       | PROTECT, null/blank | Future (entity chưa thiết kế)                                               |
| 11  | `lot`            | CharField(50)              | null/blank          | **Future** — chừa sẵn cho trace theo lô (xem D8)                            |
| 12  | `reversal_of`    | FK self                    | PROTECT, null/blank | Dòng ngược dấu trỏ về dòng gốc khi hủy phiếu                                |
| 13  | `reason`         | TextField                  | blank               | Lý do (hủy phiếu, chênh lệch kiểm kê)                                       |
| 14  | `created_by`     | FK → `iam.User`            | PROTECT, required   | Ai thực hiện thao tác (chốt/hủy phiếu)                                      |
| 15  | `created_at`     | DateTimeField              | auto_now_add        | Thời điểm hệ thống ghi sổ                                                   |

> **Không có `updated_at`** — dòng sổ kho là bất biến: không update, không delete (D2).

### 2.1 Ràng buộc "đúng 1 nguồn phiếu"

Mỗi dòng sổ kho phải có **đúng 1** trong 3 FK nguồn (`inbound_note` / `outbound_note` / `stocktake_note`) — xem D10 về lý do chọn 3 FK nullable thay vì GenericForeignKey hay tách bảng.

> **Phase 1 (thực tế lúc code):** model chỉ có `inbound_note` **NOT NULL** — 2 FK kia chưa tồn tại nên **không có NULL nào** trong sổ kho. Bảng 15 field trên là hình dạng đích khi đủ 3 loại phiếu. Triển khai CheckConstraint "đúng 1 nguồn" dần theo phase: phase 1 là `inbound_note` required; phase 2/3 thêm FK và siết constraint.

### 2.2 Phụ thuộc trường theo loại dòng

Một số trường chỉ có nghĩa với loại dòng nhất định — siết bằng `CheckConstraint` ngay từ phase 1:

| Constraint                  | Điều kiện                                                                                                |
| --------------------------- | -------------------------------------------------------------------------------------------------------- |
| Giá chỉ cho nhập mua        | `unit_price IS NOT NULL` ⇔ `movement_type = inbound_purchase_from_supplier`                            |
| Lý do chỉ cho dòng đặc biệt | `reason` chỉ bắt buộc với dòng `reversal` / `stocktake_adjustment` (validate ở service layer, không ép ở DB) |

### 2.3 `__str__`

```python
def __str__(self):
    return f"{self.movement_type} {self.material.code} {self.quantity:+.3f} @ {self.warehouse.code}"
```

## 3. Enums / Choices

```python
class StockMovement(models.Model):
    class Type(models.TextChoices):
        INBOUND_PURCHASE_FROM_SUPPLIER    = "inbound_purchase_from_supplier",    "Nhập kho: mua hàng từ nhà cung cấp"
        INBOUND_RETURN_FROM_SITE          = "inbound_return_from_site",          "Nhập kho: công trường trả lại hàng"
        OUTBOUND_ISSUE_FOR_USE            = "outbound_issue_for_use",            "Xuất kho: cấp phát để sử dụng"
        OUTBOUND_TRANSFER_TO_WAREHOUSE    = "outbound_transfer_to_warehouse",    "Xuất kho: điều chuyển sang kho khác"
        INBOUND_TRANSFER_FROM_WAREHOUSE   = "inbound_transfer_from_warehouse",   "Nhập kho: điều chuyển từ kho khác"
        STOCKTAKE_ADJUSTMENT              = "stocktake_adjustment",              "Điều chỉnh tồn: chênh lệch kiểm kê"
```

**Quy ước đặt tên (v1.2):** giá trị bắt đầu bằng hướng tồn kho — `inbound_` (vào kho, +), `outbound_` (ra khỏi kho, −), `stocktake_` (dấu tùy chênh lệch). Phần sau nói rõ lý do + đối tượng liên quan. Tên cũ (vd `inbound_return` / "Nhập hoàn trả") gây hiểu nhầm "trả hàng cho NCC" nên đã đổi.

## 4. Tồn kho (derived — không phải bảng)

| Khái niệm             | Cách tính                                                                              |
| --------------------- | -------------------------------------------------------------------------------------- |
| Tồn theo kho + vật tư | `SUM(quantity)` các dòng theo `(warehouse, material)`                                  |
| Giá trị tồn (F5)      | `quantity ×` **giá nhập gần nhất** = `unit_price` của dòng `inbound_purchase_from_supplier` mới nhất |
| Báo cáo N–X–T kỳ      | Tổng theo `date` trong khoảng, tách theo dấu / loại                                    |
| Trace-back            | Mỗi dòng trỏ về phiếu nguồn → NCC, giá, ngày, người lập                                |

Các phép tính này là query aggregate trên `StockMovement` (có index `(warehouse, material, date)`). Ở quy mô ~10 người, vài trăm vật tư, SQLite/Postgres xử lý trong ms — **chưa cần bảng cache tồn** (ADR-0001).

## 5. Quan hệ

| Entity đích                       | Cardinality | Mô tả                          | Ghi chú |
| --------------------------------- | ----------- | ------------------------------ | ------- |
| `StockMovement` → `Material`      | N → 1       | Dòng sổ kho là 1 vật tư        |         |
| `StockMovement` → `Warehouse`     | N → 1       | Dòng sổ kho thuộc 1 kho        |         |
| `StockMovement` → `InboundNote`   | N → 1       | Nguồn: phiếu nhập (phase 1)    |         |
| `StockMovement` → `StockMovement` | N → 1       | `reversal_of` — dòng ngược dấu |         |
| `InboundNote` → `StockMovement`   | 1 → N       | 1 phiếu chốt → N dòng sổ kho   |         |

## 6. Quyết định thiết kế

| #       | Quyết định                                                                             | Lý do                                                                                                                                                                                                                                                                                                                                                                                  |
| ------- | -------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **D1**  | **Sổ kho là nguồn sự thật duy nhất — không có bảng tồn**                               | Xem ADR-0001. Cần báo cáo kỳ (F5), trace-back, hủy phiếu không lệch tồn. Bảng tồn ghi đè không đáp ứng được.                                                                                                                                                                                                                                                                           |
| **D2**  | **Dòng sổ kho bất biến — không update, không delete**                                  | Giống sổ giấy: ghi rồi là còn. Mọi sửa sai đều là "ghi dòng ngược dấu" → lịch sử nguyên vẹn cho kế toán, tổng luôn khớp.                                                                                                                                                                                                                                                               |
| **D3**  | **`quantity` có dấu (+, −)**                                                           | Một cột duy nhất, `SUM` ra tồn ngay — không cần 2 cột in/out.                                                                                                                                                                                                                                                                                                                          |
| **D4**  | **Tồn tính theo kho, KHÔNG có Location**                                               | Nhất quán Warehouse D1 (YAGNI): kho thực tế là bãi chứa, không kệ/khu. Tồn = theo `(warehouse, material)`.                                                                                                                                                                                                                                                                             |
| **D5**  | **`unit_price` chỉ lưu cho `inbound_purchase_from_supplier`**        | Giá chỉ có ý nghĩa khi nhập mua. "Giá nhập gần nhất" (F5) = query dòng nhập mua mới nhất. Dòng hoàn trả/xuất không có giá. |
| **D6**  | **`date` là ngày nghiệp vụ riêng, không dùng `created_at` cho báo cáo**                | Thủ kho có thể nhập bù phiếu hôm qua. Báo cáo kỳ phải theo ngày phiếu (nghiệp vụ), còn `created_at` chỉ để audit thao tác hệ thống.                                                                                                                                                                                                                                                    |
| **D7**  | **Phân pha: phase 1 chỉ FK `inbound_note`**                                            | `OutboundNote`, `StocktakeNote` chưa thiết kế. Ràng buộc "đúng 1 nguồn" bổ sung dần theo phase — tránh model rỗng bây giờ.                                                                                                                                                                                                                                                             |
| **D8**  | **Cột `lot` chừa sẵn (nullable)**                                                      | User chốt: trace theo lô là future scope (charter §5.3). Chừa cột ngay từ đầu để sau này không phải viết lại sổ kho.                                                                                                                                                                                                                                                                   |
| **D9**  | **Không có API tạo/sửa/xóa dòng sổ kho trực tiếp**                                     | Dòng sổ kho chỉ sinh ra qua hành động **chốt/hủy phiếu** — không cho ai (kể cả admin) ghi sổ tay. Mọi thay đổi tồn đều phải có phiếu + lý do.                                                                                                                                                                                                                                          |
| **D10** | **3 FK nguồn nullable (concrete FKs) — KHÔNG dùng GenericForeignKey, không tách bảng** | Biết trước danh sách nguồn (3 loại phiếu, cố định). FK thật giữ toàn vẹn tham chiếu + filter/select_related được; GenericForeignKey mất toàn vẹn và không query được (Django docs); tách 3 bảng thì mọi query tồn thành UNION — phá vỡ ý tưởng 1 sổ kho duy nhất. 2/3 cột NULL mỗi dòng là chi phí lưu trữ không đáng kể. Phase 1 còn không có NULL nào (chỉ `inbound_note` NOT NULL). |

## 7. Backlog (tương lai)

| Mục                   | Ghi chú                                                                          |
| --------------------- | -------------------------------------------------------------------------------- |
| `Lot` (trace theo lô) | Hạn sử dụng xi măng, chứng chỉ lô thép — dùng cột `lot` đã chừa sẵn              |
| `StockAlert`          | Ngưỡng cảnh báo tồn thấp theo kho+vật tư (F5) — trước đây gọi là `MaterialStock` |
| Bảng cache tồn        | Chỉ thêm nếu query tổng chậm ở quy mô lớn                                        |
