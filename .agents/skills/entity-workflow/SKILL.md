---
name: entity-workflow
description: "Workflow design-first cho con-wms: khi thêm entity hoặc tính năng mới, agent PHẢI tạo tài liệu thiết kế trong docs/entities/<name>/ trước khi code, validate với Context7 docs, và check off implementation checklist sau khi code xong. Dùng khi user yêu cầu 'thêm entity X', 'thiết kế model Y', 'triển khai chức năng Z'."
---

# Entity Workflow — con-wms

Quy trình bắt buộc khi thêm bất kỳ entity hoặc tính năng mới vào dự án con-wms.

## Quy trình 4 bước

### Bước 1: Thiết kế (Design-first)

Tạo thư mục `docs/entities/<entity-name>/` với các file sau (dùng template trong `templates/`):

| File                | Bắt buộc? | Nội dung                                                 |
| ------------------- | --------- | -------------------------------------------------------- |
| `README.md`         | ✅        | Index trỏ đến các file con                               |
| `model.md`          | ✅        | Fields, enums, relationships, design decisions           |
| `api.md`            | ✅*       | API endpoints spec (nếu entity expose API)               |
| `auth.md`           | ⬜        | Permissions, token claims (chỉ nếu entity có auth riêng) |
| `implementation.md` | ✅        | Checklist triển khai dạng checkbox                       |
| `change-log.md`     | ✅        | Lịch sử phiên bản thiết kế                               |

> \* `api.md` có thể bỏ qua nếu entity không expose REST endpoint riêng.

Sau khi viết xong design, cập nhật `docs/entities/README.md` (index tổng) để thêm entity mới vào bảng.

### Bước 2: Validate (Context7)

Trước khi đề xuất code, tra cứu Context7 các library liên quan để xác nhận thiết kế hợp lệ:

- Django model fields, relationships → `/websites/djangoproject_en_6_0`
- DRF serializers, views, permissions → `/websites/django-rest-framework`
- JWT, auth → `/jazzband/djangorestframework-simplejwt` (nếu liên quan)
- Khác → resolve library ID phù hợp

Ghi nhận kết quả validate vào `change-log.md`.

### Bước 3: Chờ user duyệt

**Không code khi chưa có xác nhận từ user.** Trình bày thiết kế, hỏi user có muốn sửa gì không. Chỉ code sau khi user đồng ý.

### Bước 4: Triển khai + Check off

1. Code theo đúng `implementation.md`
2. Sau mỗi mục hoàn thành, đánh dấu `[x]` trong checklist
3. Báo cáo cho user những mục đã done + những mục còn lại

## Template files

Tất cả template nằm trong `templates/`. Khi tạo entity mới, copy template và điền nội dung cụ thể.

## Ví dụ entity đã làm

Xem `docs/entities/user/` — entity User đã được thiết kế và tách file đúng chuẩn này.
