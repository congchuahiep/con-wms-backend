# Site Warehouse (Kho Công Trường) — Index

> Tính năng: mỗi công trường (`Site`) có **đúng 1 kho liên kết** (`Warehouse.site` 1-1), **tự động tạo** khi tạo công trường — hỗ trợ luồng nghiệp vụ **"NCC giao thẳng tới công trường"** (mua hàng nhập thẳng, không qua kho chính).
> Django apps: `sites` (tự động tạo) + `warehouse` (thêm FK `site`) + `inventory` (tận dụng luồng phiếu có sẵn, **không đổi model**).

## Tài liệu

| File                                     | Nội dung                                                          |
| ---------------------------------------- | ----------------------------------------------------------------- |
| [`model.md`](model.md)                   | Model `Warehouse.site` 1-1, auto-create khi tạo Site, luồng phiếu |
| [`api.md`](api.md)                       | API thay đổi: Site trả kèm kho, Warehouse trả kèm công trường     |
| [`implementation.md`](implementation.md) | Checklist triển khai backend + frontend + seed                    |
| [`change-log.md`](change-log.md)         | Quyết định thiết kế chốt với user + kết quả validate Context7     |

## Bối cảnh & quyết định

Model cũ giả định mọi hàng hóa phải qua **kho chính** rồi mới "xuất ra công trường". Thực tế NCC **giao thẳng tới công trường** rất phổ biến (có khi nhiều hơn mua về kho). Quyết định chốt với user (2026-09-19):

> **Cách C (điều chỉnh):** công trường có 1 kho riêng (kho công trường) — quan hệ **1-1**, **tự động tạo** khi tạo công trường mới. Không quản lý vị trí trong kho (kho = bãi chứa phẳng). Công trường chủ yếu cần **theo dõi số lượng vật tư đã nhập**.

Phân tích 3 phương án (A/B/C) ghi trong [`change-log.md`](change-log.md).
