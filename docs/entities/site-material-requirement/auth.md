# Auth — Site Material Requirement (Định mức vật tư công trường)

## 1. Nguyên tắc

Không tạo permission mới — theo đúng mô hình `SiteViewSet` hiện có:

| Phân loại            | Endpoint                                                        | Permission                      |
| -------------------- | --------------------------------------------------------------- | ------------------------------- |
| Đọc                  | `GET /api/sites/` · `GET /api/sites/{id}/` · `GET /api/sites/{id}/requirements/` | `IsAuthenticated` |
| Ghi (master data)    | `PUT /api/sites/{id}/requirements/`                              | `IsAdmin`                       |
| Ghi (vận hành)       | `POST /api/sites/{id}/settle/`                                   | `IsAdmin`                       |
| Xóa (soft)           | `DELETE /api/sites/{id}/`                                        | `IsAdmin` (giữ nguyên)          |

## 2. Lý do

- User chốt: các thao tác quản trị công trường (tạo/sửa/xóa) vốn chỉ `IsAdmin` — định mức và tất toán là quyết định quản trị (khai báo nhu cầu, đóng công trường, chuyển kho), giữ đồng nhất để không phát sinh phân quyền phức tạp (repo đang 2 vai: đọc = authenticated, ghi = admin).
- Tất toán chạy `OutboundNote.post()` (chốt phiếu) — quyền chốt phiếu nhập/xuất hiện tại cũng nằm trong `IsAdmin` của `OutboundNoteViewSet` → không mâu thuẫn.

## 3. Backlog

- Mở quyền **thủ kho/giám sát công trường** tất toán + sửa định mức khi triển khai phân vai (RBAC) sau này — cần migration thêm `Permission`/group, nằm ngoài phạm vi v0.1.