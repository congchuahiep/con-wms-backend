# Authentication & Authorization — Supplier

## 1. Permissions

Supplier là entity data master, dùng permission pattern giống Warehouse. Không cần custom permission riêng trong app `supplier`. Dùng lại permission class từ `iam.permissions`.

| Endpoint | Permission Class | Ghi chú |
|---|---|---|
| `GET /api/suppliers/` | `IsAuthenticated` | Mọi role đã đăng nhập đều xem được danh sách NCC |
| `GET /api/suppliers/{id}/` | `IsAuthenticated` | Xem chi tiết NCC |
| `POST /api/suppliers/` | `IsAdmin` | Chỉ admin thêm NCC mới |
| `PUT /api/suppliers/{id}/` | `IsAdmin` | Chỉ admin sửa thông tin NCC |
| `DELETE /api/suppliers/{id}/` | `IsAdmin` | Chỉ admin vô hiệu hóa NCC |

**Nguyên tắc:** Read cho mọi role, Write cho admin. Thủ kho, kế toán, chủ nhiệm chỉ cần xem danh sách NCC để chọn khi tạo phiếu nhập.

## 2. Custom Permissions

Không cần thêm custom permission trong app `supplier`. Các permission trong `iam/permissions.py` đã đủ:

- `IsAdmin` — dùng cho POST/PUT/DELETE Supplier
- `IsAuthenticated` — dùng cho GET Supplier

## 3. ViewSet permission mapping

```python
# supplier/views.py
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from iam.permissions import IsAdmin


class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.filter(is_active=True)
    serializer_class = SupplierSerializer

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAdmin()]
        return [IsAuthenticated()]
```

## 4. JWT Claims

Không áp dụng — Supplier không cần nhúng thông tin vào JWT token.
