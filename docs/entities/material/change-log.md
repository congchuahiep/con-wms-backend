# Change Log — Material + Category + Unit

## v1.2 — 2026-08-07

**API trả về cây lồng đệ quy + dạng phẳng qua `?flat=true` + thêm trường `color`.**

| #   | Thay đổi                                                          | Lý do                                                                       |
| --- | ----------------------------------------------------------------- | --------------------------------------------------------------------------- |
| 1   | `GET /api/categories/` mặc định trả cây lồng đệ quy               | Hiển thị tree có toggle trên trang quản lý danh mục                         |
| 2   | `GET /api/categories/?flat=true` trả danh sách phẳng kèm `depth`  | Dùng cho select box chọn category khi tạo Material                          |
| 3   | `MaterialCategory.color` — CharField nullable (vd: "blue", "red") | Frontend hiển thị tag màu cho danh mục                                      |
| 4   | Fix `UnitConversionSerializer`: `from_unit_id` source, `required` | Trước đây cả `from_unit_id` và `to_unit_id` đều map `source="unit"`         |
| 5   | `create_conversion` view inject `from_unit_id` + `material_id`    | Serializer `PrimaryKeyRelatedField` cần data trong body dù `required=False` |

## v1.1 — 2026-08-07

**Thay đổi permission: Thủ kho được toàn quyền quản lý catalog.**

| #   | Thay đổi                                                           | Lý do                                                                                                                        |
| --- | ------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------- |
| 1   | Category/Unit/Conversion Write: `IsAdmin` → `IsAdminOrStorekeeper` | Thủ kho nhận vật tư mới → cần tạo danh mục/đơn vị/quy đổi kèm theo. Không nên block workflow nhập kho chỉ vì thiếu danh mục. |
| 2   | Material Update/Delete: `IsAdmin` → `IsAdminOrStorekeeper`         | Nhất quán với phần còn lại của catalog. Thủ kho có thể sửa/xóa vật tư họ đã tạo.                                             |

## v1.0 — 2026-08-05

Khởi tạo thiết kế: 4 models trong app `catalog`.

| #   | Thay đổi                                                      | Lý do                                                           |
| --- | ------------------------------------------------------------- | --------------------------------------------------------------- |
| 1   | `MaterialCategory` dạng tree qua `parent` FK self-referential | Quy mô nhỏ (20–30 danh mục), không cần dependency ngoài         |
| 2   | `Unit` là model riêng (không enum)                            | Sếp muốn linh hoạt thêm đơn vị + quy đổi không cần migrate      |
| 3   | `UnitConversion` với `material` FK nullable                   | NULL = quy đổi toàn cục, có set = quy đổi riêng cho vật tư      |
| 4   | FK dùng `on_delete=PROTECT` cho Category/Unit                 | Bảo vệ toàn vẹn dữ liệu, không cho xóa khi đang được tham chiếu |
| 5   | `UnitConversion.material` dùng `CASCADE`                      | Khi xóa Material, xóa luôn quy đổi riêng (quy đổi toàn cục giữ) |
| 6   | **Không** có `min_stock_alert` trên Material                  | Ngưỡng cảnh báo phụ thuộc vào kho → backlog `MaterialStock`     |
| 7   | FK output trả về nested object `{id, code, name}`             | Tránh client phải gọi thêm API để lấy tên danh mục/đơn vị       |
| 8   | Category + Unit không paginate                                | Dữ liệu ít, giống pattern Warehouse                             |

## Backlog

| Entity            | App         | Ghi chú                                                                                           |
| ----------------- | ----------- | ------------------------------------------------------------------------------------------------- |
| `MaterialStock`   | `inventory` | Tồn kho theo kho + ngưỡng cảnh báo (`warehouse FK`, `material FK`, `quantity`, `min_stock_alert`) |
| `Project`         | `project`   | Dự án xây dựng                                                                                    |
| `ProjectMaterial` | `project`   | Định mức vật tư theo dự án                                                                        |
