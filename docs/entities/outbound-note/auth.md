# Authentication & Authorization — Outbound Note

## 1. Permissions

Giống InboundNote — nghiệp vụ của **thủ kho**:

| Endpoint | Permission Class | Ghi chú |
|---|---|---|
| `GET /api/outbound-notes/` | `IsAuthenticated` | Mọi role xem được (kế toán cần xem lịch sử xuất) |
| `GET /api/outbound-notes/{id}/` | `IsAuthenticated` | Xem chi tiết phiếu |
| `POST /api/outbound-notes/` | `IsAdminOrStorekeeper` | Thủ kho + admin tạo phiếu (nháp) |
| `PUT /api/outbound-notes/{id}/` | `IsAdminOrStorekeeper` | Sửa — **chỉ phiếu nháp** (business rule trong view) |
| `DELETE /api/outbound-notes/{id}/` | `IsAdminOrStorekeeper` | Xóa — **chỉ phiếu nháp** |
| `POST /api/outbound-notes/{id}/post/` | `IsAdminOrStorekeeper` | Chốt phiếu (tự chốt, không cần duyệt) |
| `POST /api/outbound-notes/{id}/void/` | `IsAdminOrStorekeeper` | Hủy phiếu — **bắt buộc lý do** |

**Nguyên tắc (chốt với user 2026-08-13):** thủ kho tự lập và tự chốt phiếu. Phiếu đã chốt không sửa/xóa được — sai thì **hủy** (bắt buộc lý do, ghi `voided_by`/`voided_at` + dòng sổ kho ngược dấu) rồi lập phiếu mới. Kế toán chỉ xem.

## 2. Custom Permissions

Không cần custom permission mới — dùng lại từ `iam/permissions.py`:

- `IsAdminOrStorekeeper` — mọi thao tác ghi trên OutboundNote
- `IsAuthenticated` — GET OutboundNote

## 3. ViewSet permission mapping

```python
# inventory/views.py
class OutboundNoteViewSet(viewsets.ModelViewSet):
    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy", "post", "void"):
            return [IsAdminOrStorekeeper()]
        return [IsAuthenticated()]

    @action(detail=True, methods=["post"])
    def post(self, request, pk=None):          # chốt → check tồn + ghi sổ kho
        ...

    @action(detail=True, methods=["post"])
    def void(self, request, pk=None):          # hủy → dòng sổ kho ngược dấu
        ...
```

## 4. JWT Claims

Không áp dụng — Outbound Note không cần nhúng thông tin vào JWT token.
