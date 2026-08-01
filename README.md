# con-wms

Hệ thống quản lý vật tư (Warehouse Management System) cho công ty xây dựng địa phương (quy mô nhỏ).

## Tài liệu

- [`docs/PROJECT_CHARTER.md`](docs/PROJECT_CHARTER.md) — Project Charter & Scope (mục tiêu, phạm vi, yêu cầu phi chức năng, cột mốc).

## Stack

- **Backend:** Django 6 + Django REST Framework + simpleJWT + django-filter + drf-spectacular (OpenAPI).
- **Frontend:** Next.js (App Router) + TailwindCSS (chưa khởi tạo).
- **Barcode:** đầu đọc USB HID (giả lập bàn phím).
- **DB:** SQLite (bản đầu), sẵn sàng chuyển PostgreSQL.

## Trạng thái

Đang ở giai đoạn chuẩn bị tài liệu thiết kế. Xem [`docs/PROJECT_CHARTER.md`](docs/PROJECT_CHARTER.md) để biết phạm vi và cột mốc.
