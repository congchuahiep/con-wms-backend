# Model — Material + Category + Unit

> Django app: `catalog`
> Kế thừa: `models.Model`

## 1. Bối cảnh thực tế

Công ty xây dựng địa phương (~10 người, 1–3 kho). Vật tư bao gồm: xi măng (bao), thép (cây/kg/tấn), cát (m3), đá (m3), gạch (viên)... Mỗi loại có đơn vị tính riêng, và nhiều đơn vị có thể quy đổi qua lại (1 tấn = 1000 kg, 1 bao xi măng = 50 kg).

Sếp yêu cầu hệ thống phải quy đổi được đơn vị (vd: nhập 200 bao xi măng → hệ thống biết = 10,000 kg). Thiết kế đáp ứng yêu cầu này qua model `UnitConversion`.

Danh mục vật tư dạng phân cấp (tree) qua self-referential FK, đủ dùng cho quy mô 20–30 danh mục, không cần thêm dependency như django-mptt.

> **Nguyên tắc:** Entity `Material` chỉ trả lời câu hỏi **"vật tư này là gì?"** — không trả lời **"còn bao nhiêu?"** (→ `MaterialStock` backlog) hay **"dự án cần bao nhiêu?"** (→ `ProjectMaterial` backlog).

## 2. Models

_(code Python giữ nguyên như bản trước, không thay đổi)_

## 3. Quan hệ tổng thể

```
MaterialCategory (tree: parent FK → self)
    │ 1→N
    ▼
Material ──FK──▶ Unit
    │              ▲
    │              │ 1→N
    │              │
    └──▶ UnitConversion (from_unit FK, to_unit FK)
              │
              └── material (nullable FK → Material)
```

## 4. Enums / Choices

Không có enum riêng. Các đơn vị tính được lưu dưới dạng model `Unit` thay vì `TextChoices` để:

- Cho phép thêm đơn vị mới không cần migrate
- Hỗ trợ quy đổi đơn vị linh hoạt qua `UnitConversion`

## 5. Quyết định thiết kế

| #        | Quyết định                                       | Lý do                                                                                                                                                                                                                                    |
| -------- | ------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **D1**   | **Category dạng tree qua self-referential FK**   | Quy mô 20–30 danh mục, không cần dependency django-mptt. `parent=null` là root.                                                                                                                                                          |
| **D1.1** | **Category có trường `color`**                   | Lưu chuỗi màu (vd: "blue", "red", "green") để frontend hiển thị tag màu cho từng danh mục. Nullable, không bắt buộc.                                                                                                                     |
| **D2**   | **Unit là model riêng, không phải enum**         | Sếp muốn linh hoạt thêm đơn vị + quy đổi. Model riêng cho phép CRUD unit qua API không cần migrate.                                                                                                                                      |
| **D3**   | **UnitConversion.material nullable**             | NULL = quy đổi toàn cục (1 tấn = 1000 kg). Có set = quy đổi riêng cho vật tư đó (1 bao XM Hà Tiên = 50 kg).                                                                                                                              |
| **D4**   | **FK dùng on_delete=PROTECT**                    | Không cho xóa Category/Unit đang được Material/Conversion tham chiếu → bảo vệ toàn vẹn dữ liệu.                                                                                                                                          |
| **D5**   | **UnitConversion dùng CASCADE khi xóa Material** | Nếu xóa vật tư, xóa luôn quy đổi riêng của nó (quy đổi toàn cục vẫn giữ).                                                                                                                                                                |
| **D6**   | **Không có `min_stock_alert` trên Material**     | Ngưỡng cảnh báo phụ thuộc vào kho → thuộc về `MaterialStock` (backlog).                                                                                                                                                                  |
| **D7**   | **Timestamps `created_at` + `updated_at`**       | Chuẩn cho mọi entity, hỗ trợ audit trail.                                                                                                                                                                                                |
| **D8**   | **`description` trên Material**                  | Ghi chú kỹ thuật: quy cách, thông số, hãng sản xuất. Phân biệt với `note` (ghi chú nghiệp vụ) sẽ có ở các entity inventory.                                                                                                              |
| **D9**   | **UnitConversion KHÔNG tạo ra Unit mới**         | `1 BAO = 50 KG (XM Hà Tiên)` là quy đổi, không phải tạo Unit mới tên "bao xi măng". Tạo Unit riêng cho từng combo sẽ làm bảng Unit phình to. `UnitConversion` giữ bảng Unit gọn (5–10 dòng), mọi biến thể quy đổi nằm ở bảng conversion. |
| **D10**  | **Material nhận `conversions` nested write**     | Form Material tạo/sửa luôn `UnitConversion` riêng atomic (1 request). `from_unit` luôn = `material.unit`; `to_unit` = `toUnitId` client gửi. Không đổi model `UnitConversion` — chỉ thêm tầng serializer/view.                           |

## 6. Backlog (tương lai)

| Entity            | App         | Mô tả                                                                                  |
| ----------------- | ----------- | -------------------------------------------------------------------------------------- |
| `MaterialStock`   | `inventory` | Tồn kho theo kho (`warehouse FK` + `material FK` + `quantity` + `min_stock_alert`)     |
| `Project`         | `project`   | Dự án xây dựng (`code`, `name`, `warehouse FK`)                                        |
| `ProjectMaterial` | `project`   | Định mức vật tư theo dự án (`project FK` + `material FK` + `planned_qty` + `used_qty`) |
