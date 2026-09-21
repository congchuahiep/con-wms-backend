# Site Material Requirement — Định mức vật tư công trường

> Tính năng A: công trường khai báo **cần những vật tư gì, số lượng bao nhiêu** → hệ thống dùng làm **mốc so sánh** với tồn kho của kho công trường (KHÔNG giới hạn việc nhập thêm vật tư ngoài định mức). Khi công trường đủ định mức và hoàn thành → chức năng **Tất toán** đưa phần vật tư thừa/ngoài định mức về một kho khác còn hoạt động.

## Trạng thái

- 📝 **v0.1 — design xong (2026-09-20), chờ user duyệt (chưa code)**

## Nội dung

| File          | Nội dung                                             |
| ------------- | ---------------------------------------------------- |
| `model.md`    | Model `SiteMaterialRequirement` + `Site.status` enum + luồng tất toán |
| `api.md`      | API: danh sách so sánh, cập nhật định mức, tất toán |
| `auth.md`     | Phân quyền đọc/ghi                                      |
| `implementation.md` | Checklist triển khai (backend + frontend)        |
| `change-log.md` | Lịch sử thiết kế + kết quả validate                 |

## Phạm vi

- **Backend**: `sites` (model mới + `Site.status`), `inventory` (guard chặn phiếu vào kho đã đóng), `warehouse` (đóng kho khi tất toán).
- **Frontend** (con-wms-frontend): trang chi tiết công trường `/sites/[id]` — thông tin chung + bảng so sánh định mức vs tồn kho + dialog sửa định mức + dialog tất toán; trang danh sách cập nhật theo `status`.