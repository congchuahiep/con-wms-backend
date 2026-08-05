# Authentication & Authorization — Warehouse

## 1. Permissions

Warehouse là entity đơn giản, không cần custom permission riêng trong app `warehouse`. Dùng lại permission class từ `iam.permissions`.

| Endpoint | Permission Class | Ghi chú |
|---|---|---|
| `GET /api/warehouses/` | `IsAuthenticated` | Mọi role đã đăng nhập đều xem được danh sách kho |
| `GET /api/warehouses/{id}/` | `IsAuthenticated` | Xem chi tiết kho |
| `POST /api/warehouses/` | `IsAdmin` | Chỉ admin tạo kho mới |
| `PUT /api/warehouses/{id}/` | `IsAdmin` | Chỉ admin sửa thông tin kho |
| `DELETE /api/warehouses/{id}/` | `IsAdmin` | Chỉ admin vô hiệu hóa kho |

**Nguyên tắc:** Read cho mọi role, Write cho admin. Thủ kho không cần tạo/sửa kho (chỉ cần chọn kho khi tạo phiếu).

## 2. Custom Permissions

Không cần thêm custom permission trong app `warehouse`. Các permission trong `iam/permissions.py` đã đủ:

- `IsAdmin` — dùng cho POST/PUT/DELETE Warehouse
- `IsAuthenticated` — dùng cho GET Warehouse

## 3. ViewSet permission mapping

```python
# warehouse/views.py
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from iam.permissions import IsAdmin


class WarehouseViewSet(viewsets.ModelViewSet):
    queryset = Warehouse.objects.filter(is_active=True)
    serializer_class = WarehouseSerializer

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAdmin()]
        return [IsAuthenticated()]
```

## 4. JWT Claims

Không áp dụng — Warehouse không cần nhúng thông tin vào JWT token.
