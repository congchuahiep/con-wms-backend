# Authentication & Authorization — Stocktake Note

## 1. Permissions

Giống InboundNote/OutboundNote — nghiệp vụ của **thủ kho**:

| Endpoint | Permission Class | Ghi chú |
|---|---|---|
| `GET /api/stocktake-notes/` | `IsAuthenticated` | Mọi role xem được (kế toán cần xem biên bản kiểm kê) |
| `GET /api/stocktake-notes/{id}/` | `IsAuthenticated` | Xem chi tiết phiếu |
| `POST /api/stocktake-notes/` | `IsAdminOrStorekeeper` | Thủ kho + admin tạo phiếu (nháp) |
| `PUT /api/stocktake-notes/{id}/` | `IsAdminOrStorekeeper` | Nhập số đếm — **chỉ phiếu nháp** |
| `DELETE /api/stocktake-notes/{id}/` | `IsAdminOrStorekeeper` | Xóa — **chỉ phiếu nháp** |
| `POST /api/stocktake-notes/{id}/post/` | `IsAdminOrStorekeeper` | Chốt phiếu (tự chốt, không cần duyệt) |
| `POST /api/stocktake-notes/{id}/void/` | `IsAdminOrStorekeeper` | Hủy phiếu — **bắt buộc lý do** |

**Nguyên tắc (chốt với user 2026-08-13):** thủ kho tự lập và tự chốt phiếu. Phiếu đã chốt không sửa/xóa được — sai thì **hủy** (bắt buộc lý do, ghi `voided_by`/`voided_at` + dòng sổ kho ngược dấu) rồi lập phiếu mới. Kế toán chỉ xem.

## 2. Custom Permissions

Không cần custom permission mới — dùng lại từ `iam/permissions.py`:

- `IsAdminOrStorekeeper` — mọi thao tác ghi trên StocktakeNote
- `IsAuthenticated` — GET StocktakeNote

## 3. ViewSet permission mapping

```python
# inventory/views.py
class StocktakeNoteViewSet(viewsets.ModelViewSet):
    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy", "post", "void"):
            return [IsAdminOrStorekeeper()]
        return [IsAuthenticated()]

    @action(detail=True, methods=["post"])
    def post(self, request, pk=None):          # chốt → ghi dòng điều chỉnh chênh lệch
        ...

    @action(detail=True, methods=["post"])
    def void(self, request, pk=None):          # hủy → đảo dấu các dòng điều chỉnh
        ...
```

## 4. JWT Claims

Không áp dụng — Stocktake Note không cần nhúng thông tin vào JWT token.
