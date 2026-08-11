# Material + Category + Unit — Index

Django app: **`catalog`**

## Tài liệu

| File                                     | Nội dung                                        |
| ---------------------------------------- | ----------------------------------------------- |
| [`model.md`](model.md)                   | Thuộc tính, enums, quan hệ, quyết định thiết kế |
| [`api.md`](api.md)                       | Danh sách API endpoints + request/response spec |
| [`auth.md`](auth.md)                     | Permissions                                     |
| [`implementation.md`](implementation.md) | Checklist triển khai từng bước                  |
| [`change-log.md`](change-log.md)         | Lịch sử thay đổi thiết kế                       |

## Scope

| Entity             | Mô tả                              | Trạng thái                                                  |
| ------------------ | ---------------------------------- | ----------------------------------------------------------- |
| `MaterialCategory` | Danh mục vật tư phân cấp (tree)    | ✅ Done                                                     |
| `Unit`             | Đơn vị tính (bao, kg, m3...)       | 🔀 **Đã tách** → [`docs/entities/unit/`](../unit/README.md) |
| `UnitConversion`   | Quy đổi đơn vị (1 tấn = 1000 kg)   | 🔀 **Đã tách** → [`docs/entities/unit/`](../unit/README.md) |
| `Material`         | Vật tư (xi măng, thép, cát...)     | ✅ Done                                                     |
| `MaterialStock`    | Tồn kho theo kho + ngưỡng cảnh báo | 📋 Backlog (app `inventory`)                                |
| `ProjectMaterial`  | Định mức vật tư theo dự án         | 📋 Backlog (app `project`)                                  |
