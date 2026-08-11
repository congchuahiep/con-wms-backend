# Unit + UnitConversion — Index

Django app: **`catalog`**

## Tài liệu

| File                                     | Nội dung                                        |
| ---------------------------------------- | ----------------------------------------------- |
| [`model.md`](model.md)                   | Thuộc tính, enums, quan hệ, quyết định thiết kế |
| [`api.md`](api.md)                       | Danh sách API endpoints + request/response spec |
| [`auth.md`](auth.md)                     | Permissions                                     |
| [`implementation.md`](implementation.md) | Checklist triển khai từng bước                  |
| [`change-log.md`](change-log.md)         | Lịch sử thay đổi thiết kế                       |
| [`frontend-migration.md`](frontend-migration.md) | Hướng dẫn FE cập nhật theo thiết kế mới  |

## Scope

| Entity           | Mô tả                                                     | Trạng thái         |
| ---------------- | --------------------------------------------------------- | ------------------ |
| `Unit`           | Đơn vị tính + `conversion_type` (global / material)       | 🔵 Thiết kế lần này |
| `UnitConversion` | Quy đổi đơn vị (1 chiều + reverse virtual cho global)     | 🔵 Thiết kế lần này |

## Tách khỏi Material

Trước đây Unit + UnitConversion được thiết kế chung với Material trong
[`docs/entities/material/`](../material/README.md). Lần refactor này tách ra
thành entity riêng vì phạm vi thay đổi lớn: thêm `conversion_type`,
reverse virtual, gộp response.
