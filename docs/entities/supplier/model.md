# Model — Supplier (Nhà Cung Cấp)

> Django app: `supplier`
> Kế thừa: `models.Model`

## 1. Bối cảnh thực tế

Công ty xây dựng địa phương làm việc với một số nhà cung cấp vật liệu quen thuộc: đại lý xi măng, cửa hàng sắt thép, trạm trộn bê tông... Mỗi nhà cung cấp có người liên hệ, số điện thoại, email để đặt hàng. Đây là entity data master đơn giản — chỉ cần lưu thông tin liên hệ, không cần quan hệ phức tạp với các entity khác ở thời điểm hiện tại.

Thiết kế theo pattern **Warehouse**: CRUD phẳng, soft delete, không enum.

## 2. Model

### 2.1 Thuộc tính

| #   | Field            | Kiểu              | Ràng buộc             | Ghi chú |
| --- | ---------------- | ----------------- | --------------------- | ------- |
| 1   | `id`             | BigAutoField (PK) |                       | Django mặc định |
| 2   | `code`           | CharField(20)     | **unique**            | Mã NCC: `NCC001`, `NCC002` |
| 3   | `name`           | CharField(200)    | required              | Tên đầy đủ (vd: "Công ty TNHH Vật Liệu Xây Dựng ABC") |
| 4   | `tax_code`       | CharField(20)     | **unique**, blank=True | Mã số thuế (MST) |
| 5   | `contact_person` | CharField(100)    | blank=True            | Người liên hệ (vd: "Anh Tuấn — quản lý bán hàng") |
| 6   | `phone`          | CharField(20)     | blank=True            | SĐT liên hệ |
| 7   | `email`          | EmailField        | blank=True            | Email liên hệ |
| 8   | `address`        | TextField         | blank=True            | Địa chỉ văn phòng / cửa hàng |
| 9   | `note`           | TextField         | blank=True            | Ghi chú chung (vd: "Giao hàng thứ 3-5-7", "Giá tốt, nhưng hay giao trễ") |
| 10  | `is_active`      | BooleanField      | default=True          | Soft delete — NCC ngừng hợp tác |
| 11  | `created_at`     | DateTimeField     | auto_now_add          | |
| 12  | `updated_at`     | DateTimeField     | auto_now              | |

### 2.2 `tax_code` — Mã số thuế

- Kiểu: `CharField(max_length=20)`, `unique=True`, `blank=True`
- **Unique** — mỗi NCC có 1 MST duy nhất. Blank allowed cho NCC chưa có MST
- Không validate format (MST Việt Nam: 10 hoặc 14 chữ số, có dấu gạch ngang) — YAGNI, để tự do cho người dùng

### 2.3 Enums / Choices

Không có enum riêng cho Supplier. Entity này không có trường nào cần `TextChoices` / `IntegerChoices`.

### 2.4 `__str__`

```python
def __str__(self):
    return f"{self.code} — {self.name}"
```

## 3. Quan hệ

| Entity đích    | Cardinality | Mô tả                              | Ghi chú |
| -------------- | ----------- | ---------------------------------- | ------- |
| `InboundNote`  | 1 → N       | Phiếu nhập từ NCC này              | Entity tương lai (`inventory` app) |
| `PurchaseOrder`| 1 → N       | Đơn đặt hàng tới NCC này           | Entity tương lai (chưa xác định app) |

## 4. Quyết định thiết kế

| #      | Quyết định                                | Lý do |
| ------ | ----------------------------------------- | ----- |
| **D1** | **`tax_code` unique, blank=True**         | Mỗi NCC có 1 MST duy nhất. Blank=True để hỗ trợ NCC chưa có MST (vd: hộ kinh doanh nhỏ). Django coi NULL/blank là không conflict với unique constraint. |
| **D2** | **`code` unique toàn cục**                | Pattern giống Warehouse. `NCC001`, `NCC002` dễ nhớ, dropdown chọn NCC không bị nhầm. |
| **D3** | **Soft delete qua `is_active`**           | Không xóa cứng NCC đã có phiếu nhập. Tương tự pattern của `User.is_active` và `Warehouse.is_active`. |
| **D4** | **Không FK tới `User` cho `contact_person`** | `contact_person` là text field tự do, không phải user trong hệ thống. Người liên hệ của NCC là người bên ngoài công ty. |
| **D5** | **Timestamps `created_at` + `updated_at`** | Chuẩn cho mọi entity trong hệ thống, hỗ trợ audit trail cơ bản. |
| **D6** | **Không validate format phone/email/tax** | YAGNI. Để Django EmailField validate email cơ bản là đủ. Phone và tax_code để tự do — tránh block người dùng vì format không khớp regex cứng nhắc. |
