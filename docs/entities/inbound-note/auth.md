# Authentication & Authorization — Inbound Note

## 1. Permissions

Inbound Note là nghiệp vụ của **thủ kho** — khác với master data (Warehouse/Supplier: write = admin). Thủ kho là người tạo phiếu nhập hàng ngày.

| Endpoint | Permission Class | Ghi chú |
|---|---|---|
| `GET /api/inbound-notes/` | `IsAuthenticated` | Mọi role xem được (kế toán cần xem lịch sử giao dịch NCC) |
| `GET /api/inbound-notes/{id}/` | `IsAuthenticated` | Xem chi tiết phiếu |
| `POST /api/inbound-notes/` | `IsAdminOrStorekeeper` | Thủ kho + admin tạo phiếu (nháp) |
| `PUT /api/inbound-notes/{id}/` | `IsAdminOrStorekeeper` | Thủ kho + admin sửa — **chỉ phiếu nháp** (business rule trong view) |
| `DELETE /api/inbound-notes/{id}/` | `IsAdminOrStorekeeper` | Thủ kho + admin xóa — **chỉ phiếu nháp** |
| `POST /api/inbound-notes/{id}/post/` | `IsAdminOrStorekeeper` | Thủ kho + admin chốt phiếu (tự chốt, không cần duyệt) |
| `POST /api/inbound-notes/{id}/void/` | `IsAdminOrStorekeeper` | Thủ kho + admin hủy phiếu — **bắt buộc lý do** |

**Nguyên tắc (chốt với user 2026-08-13):** thủ kho tự nhập và tự chốt phiếu. Phiếu đã chốt không sửa/xóa được — sai thì **hủy** (thủ kho + admin, bắt buộc lý do, hệ thống ghi `voided_by`/`voided_at` + dòng sổ kho ngược dấu) rồi lập phiếu mới. Kế toán chỉ xem.

## 2. Custom Permissions

Không cần custom permission mới — dùng lại từ `iam/permissions.py`:

- `IsAdminOrStorekeeper` — mọi thao tác ghi trên InboundNote
- `IsAuthenticated` — GET InboundNote

## 3. ViewSet permission mapping

```python
# inventory/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from iam.permissions import IsAdminOrStorekeeper


class InboundNoteViewSet(viewsets.ModelViewSet):
    queryset = InboundNote.objects.all()
    serializer_class = InboundNoteSerializer

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy", "post", "void"):
            return [IsAdminOrStorekeeper()]
        return [IsAuthenticated()]

    @action(detail=True, methods=["post"])
    def post(self, request, pk=None):          # chốt phiếu → ghi sổ kho
        ...

    @action(detail=True, methods=["post"])
    def void(self, request, pk=None):          # hủy phiếu → dòng sổ kho ngược dấu
        ...
```

## 4. JWT Claims

Không áp dụng — Inbound Note không cần nhúng thông tin vào JWT token.
