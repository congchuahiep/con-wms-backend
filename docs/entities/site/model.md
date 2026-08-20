# Model — Site (Công Trường)

> Django app: `sites`
> Kế thừa: `models.Model`

## 1. Bối cảnh thực tế

Công ty xây dựng có nhiều **công trường** (nơi thi công nhận vật tư): cầu Rạch Giá, kè Sông Bé, nhà dân... Vật tư được **xuất kho cấp cho công trường** (`OutboundNote`), và có thể được **công trường trả lại kho** (`InboundNote` loại `return_from_site`).

Lúc đầu thiết kế `OutboundNote.destination` là free text — nhưng dự án **có báo cáo công trường** (user xác nhận 2026-08-18), free text không lọc/tổng hợp được. Chốt: **tạo hẳn entity `Site`** — thay `destination` bằng FK, khỏi migrate sau (outbound-note D3).

## 2. Model

### 2.1 Thuộc tính

| # | Field | Kiểu | Ràng buộc | Ghi chú |
|---|---|---|---|---|
| 1 | `id` | BigAutoField (PK) | | Django mặc định |
| 2 | `code` | CharField(20) | **unique** | Mã viết tắt: `CT_RG`, `CT_KE_SONG_BE` |
| 3 | `name` | CharField(200) | required | Tên công trường (vd: "Công trường cầu Rạch Giá") |
| 4 | `manager` | CharField(100) | blank | Người phụ trách công trường (đầu mối nhận hàng) |
| 5 | `phone` | CharField(20) | blank | SĐT phụ trách |
| 6 | `address` | TextField | blank | Địa chỉ công trường |
| 7 | `note` | TextField | blank | Ghi chú (vd: "Khu vực thi công chật, xe tải lớn khó vào") |
| 8 | `is_active` | BooleanField | default=True | Soft delete — công trường đang thi công |
| 9 | `created_at` | DateTimeField | auto_now_add | |
| 10 | `updated_at` | DateTimeField | auto_now | |

### 2.2 Enums / Choices

Không có enum riêng — entity master data đơn giản, không cần `TextChoices`.

### 2.3 `__str__`

```python
def __str__(self):
    return f"{self.code} — {self.name}"
```

## 3. Quan hệ

| Entity đích | Cardinality | Mô tả | Ghi chú |
|---|---|---|---|
| `OutboundNote` | 1 → N | Phiếu xuất cấp cho công trường này (`site` FK) | `inventory` app — bắt buộc khi `issue_for_use` |
| `InboundNote` | 1 → N | Phiếu nhập trả lại từ công trường này (`site` FK) | `inventory` app — bắt buộc khi `return_from_site` (user chốt 2026-08-18) |

## 4. Quyết định thiết kế

| # | Quyết định | Lý do |
|---|---|---|
| **D1** | **`code` unique toàn cục** | Giống Warehouse D3 — ít công trường, unique toàn cục tránh nhầm lẫn khi chọn dropdown. |
| **D2** | **Soft delete qua `is_active`** | Không xóa cứng công trường đã có phiếu xuất (PROTECT từ OutboundNote). Tương tự Warehouse/Supplier. |
| **D3** | **`manager` + `phone`** | Đầu mối nhận hàng tại công trường — cần khi giao hàng / liên hệ trả hàng. Giống `contact_person` của Supplier. |
| **D4** | **Không có GPS (lat/lng)** | Khác Warehouse — công trường không cần định vị để quản lý kho. YAGNI, thêm sau nếu cần. |
| **D5** | **App name `sites`, không phải `site`** | `site` trùng module chuẩn Python — đặt tên `sites` tránh shadowing. |
| **D6** | **FK từ phiếu dùng `PROTECT`** | Nhất quán toàn dự án: không xóa được đối tượng đang được chứng từ tham chiếu (như Supplier/Warehouse). |
