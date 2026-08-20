# Authentication & Authorization — Site (Công Trường)

## 1. Permissions

Site là **master data** — giống Warehouse/Supplier: Read cho mọi role, Write cho admin.

| Endpoint | Permission Class | Ghi chú |
|---|---|---|
| `GET /api/sites/` | `IsAuthenticated` | Mọi role xem được (thủ kho cần chọn công trường khi lập phiếu xuất) |
| `GET /api/sites/{id}/` | `IsAuthenticated` | Xem chi tiết |
| `POST /api/sites/` | `IsAdmin` | Chỉ admin tạo |
| `PUT /api/sites/{id}/` | `IsAdmin` | Chỉ admin sửa |
| `DELETE /api/sites/{id}/` | `IsAdmin` | Chỉ admin vô hiệu hóa |

**Nguyên tắc:** thủ kho không cần tạo/sửa công trường (chỉ cần chọn khi tạo phiếu) — admin quản lý danh mục.

## 2. Custom Permissions

Không cần custom permission mới — dùng lại từ `iam/permissions.py`:

- `IsAdmin` — POST/PUT/DELETE Site
- `IsAuthenticated` — GET Site

## 3. ViewSet permission mapping

```python
# sites/views.py
class SiteViewSet(viewsets.ModelViewSet):
    queryset = Site.objects.filter(is_active=True)
    serializer_class = SiteSerializer

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAdmin()]
        return [IsAuthenticated()]
```

## 4. JWT Claims

Không áp dụng — Site không cần nhúng thông tin vào JWT token.
