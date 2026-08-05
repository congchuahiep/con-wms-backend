# Model — Warehouse

> Django app: `warehouse`
> Kế thừa: `models.Model`

## 1. Bối cảnh thực tế

Công ty xây dựng địa phương (xã, ~10 người, 1–3 kho). Nhà kho thực tế là **bãi chứa vật liệu** (~200m²): xi măng chất đống, ống sắt thép quăng dọc tường, vài kệ nhỏ để đồ linh tinh. **Không có kệ đánh số, không có phân khu chính thức, không có vị trí cố định** — việc tổ chức cấu trúc vị trí cứng nhắc là over-engineering ở thời điểm hiện tại.

Thiết kế áp dụng nguyên tắc **YAGNI (You Ain't Gonna Need It)**: chỉ làm Warehouse phẳng, không làm Location. Nếu sau này giám đốc yêu cầu quản lý vị trí kệ hàng, sẽ mở rộng thêm entity Location với `parent` FK (đã được dự trù trong thiết kế).

> **Tham chiếu:** `docs/PROJECT_CHARTER.md` §5.1 F3 — yêu cầu gốc "cấu trúc vị trí: Kho → Khu vực → Kệ → Tầng → Ô" — được điều chỉnh do không khớp thực tế.

## 2. Model

### 2.1 Thuộc tính

| #   | Field        | Kiểu              | Ràng buộc             | Ghi chú                                                                                                |
| --- | ------------ | ----------------- | --------------------- | ------------------------------------------------------------------------------------------------------ |
| 1   | `id`         | BigAutoField (PK) |                       | Django mặc định                                                                                        |
| 2   | `code`       | CharField(20)     | **unique**            | Mã viết tắt: `KHO_CHINH`, `KHO_PHU`                                                                    |
| 3   | `name`       | CharField(200)    | required              | Tên đầy đủ (vd: "Kho chính — Bãi sau")                                                                 |
| 4   | `address`    | TextField         | blank=True            | Địa chỉ cụ thể của kho                                                                                 |
| 5   | `note`       | TextField         | blank=True            | Ghi chú chung về kho (vd: "Đang sửa mái, cần che bạt khi mưa", "Kho thuê của ông Ba, hết hạn 12/2026") |
| 6   | `latitude`   | DecimalField(9,6) | null=True, blank=True | Vĩ độ GPS — frontend dùng Google Maps chọn vị trí                                                      |
| 7   | `longitude`  | DecimalField(9,6) | null=True, blank=True | Kinh độ GPS                                                                                            |
| 8   | `is_active`  | BooleanField      | default=True          | Soft delete — kho ngừng sử dụng                                                                        |
| 9   | `created_at` | DateTimeField     | auto_now_add          |                                                                                                        |
| 10  | `updated_at` | DateTimeField     | auto_now              |                                                                                                        |

### 2.2 `latitude` / `longitude` — độ chính xác

- Kiểu: `DecimalField(max_digits=9, decimal_places=6)`
- 6 chữ số thập phân → độ chính xác ~0.11m (11cm) — quá đủ để phân biệt 2 kho
- Cả 2 field đều `null=True, blank=True` — không phải kho nào cũng có tọa độ GPS ngay
- Frontend dùng Google Maps JavaScript API để chọn vị trí, gửi `{lat, lng}` về backend

### 2.3 Enums / Choices

Không có enum riêng cho Warehouse. Entity này không có trường nào cần `TextChoices` / `IntegerChoices`.

### 2.4 `__str__`

```python
def __str__(self):
    return f"{self.code} — {self.name}"
```

## 3. Quan hệ

| Entity đích     | Cardinality | Mô tả                                                           | Ghi chú                                                   |
| --------------- | ----------- | --------------------------------------------------------------- | --------------------------------------------------------- |
| `InboundNote`   | 1 → N       | Phiếu nhập vào kho này                                          | Entity tương lai (`inventory` app)                        |
| `OutboundNote`  | 1 → N       | Phiếu xuất từ kho này                                           | Entity tương lai (`inventory` app)                        |
| `StocktakeNote` | 1 → N       | Phiếu kiểm kê cho kho này                                       | Entity tương lai (`stocktake` app)                        |
| `MaterialStock` | 1 → N       | Tồn kho theo vật tư                                             | Entity tương lai (`inventory` app)                        |
| `Location`      | 1 → N       | **(Future)** Vị trí trong kho — nếu sau này cần quản lý kệ/ngăn | Sẽ thêm model `Location` với `parent` FK self-referential |

## 4. Quyết định thiết kế

| #      | Quyết định                                                    | Lý do                                                                                                                                                                                                           |
| ------ | ------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **D1** | **Chỉ có Warehouse, không có Location**                       | YAGNI. Thực tế kho là bãi chứa, không có kệ/khu vực cố định. Thêm Location lúc này là code thừa, gây khó cho thủ kho (phải chọn vị trí khi nhập dù thực tế không có).                                           |
| **D2** | **`note` field cho ghi chú chung về kho**                     | Ghi chú tự do về bản thân kho: tình trạng, lưu ý quản lý, thông tin thuê/mượn. **Không** dùng để ghi vị trí đặt đồ — việc đó thuộc về entity `MaterialStock` (tồn kho theo vật tư) hoặc `Location` (tương lai). |
| **D3** | **`code` unique toàn cục** (không phải unique theo warehouse) | Chỉ có 1–3 kho, unique toàn cục đủ dùng và tránh nhầm lẫn khi chọn kho trong dropdown.                                                                                                                          |
| **D4** | **Soft delete qua `is_active`**                               | Không xóa cứng kho đã có phiếu nhập/xuất. Tương tự pattern của `User.is_active`.                                                                                                                                |
| **D5** | **Timestamps `created_at` + `updated_at`**                    | Chuẩn cho mọi entity trong hệ thống, hỗ trợ audit trail cơ bản.                                                                                                                                                 |
| **D6** | **Để sẵn kế hoạch mở rộng Location**                          | Nếu sau này cần, thêm model `Location(warehouse FK, parent FK self, level_type, code, name)` — schema `parent` FK self-referential cho phép cây sâu tùy ý mà không cần migrate phức tạp. Không code ngay.       |
| **D7** | **`DecimalField(9,6)` cho lat/lng, nullable**                 | Độ chính xác 11cm — quá đủ cho cấp độ nhà kho. Nullable vì thủ kho có thể tạo kho nhanh chưa chọn vị trí trên Google Maps. Frontend tự động populate khi người dùng chọn trên bản đồ.                           |
