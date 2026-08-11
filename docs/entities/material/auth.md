# Authentication & Authorization — Catalog

## 1. Permissions

Catalog dùng lại permission class từ `iam.permissions`.

| Endpoint                                  | Permission             | Ghi chú                                    |
| ----------------------------------------- | ---------------------- | ------------------------------------------ |
| `GET` (list/retrieve) — tất cả resource   | `IsAuthenticated`      | Mọi role đã đăng nhập đều xem được         |
| `POST/PUT/PATCH/DELETE` — tất cả resource | `IsAdminOrStorekeeper` | Admin + Thủ kho toàn quyền quản lý catalog |

**Nguyên tắc:**

- Read: mọi role
- Write: Admin + Thủ kho — toàn bộ catalog (Material, Category, Unit, Conversion)

**Lý do cho Thủ kho full quyền trên catalog:**

Trong công ty xây dựng nhỏ (~10 người, 1–3 kho), admin không phải lúc nào cũng có mặt tại kho. Khi thủ kho nhận vật tư mới chưa có trong hệ thống, họ cần tự chủ hoàn toàn:

1. Tạo `MaterialCategory` mới nếu danh mục chưa tồn tại
2. Tạo `Unit` mới nếu đơn vị tính chưa có
3. Tạo `UnitConversion` nếu cần quy đổi
4. Tạo `Material`

Không nên block toàn bộ workflow nhập kho chỉ vì thiếu một danh mục hay đơn vị tính. Admin vẫn có thể audit sau qua timestamps (`created_at`, `updated_at`).

## 2. ViewSet permission mapping

```python
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from iam.permissions import IsAdminOrStorekeeper


class MaterialViewSet(viewsets.ModelViewSet):
    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAdminOrStorekeeper()]
        return [IsAuthenticated()]


class MaterialCategoryViewSet(viewsets.ModelViewSet):
    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAdminOrStorekeeper()]
        return [IsAuthenticated()]


class UnitViewSet(viewsets.ModelViewSet):
    def get_permissions(self):
        # create_conversion là @action POST dưới /units/{id}/conversions/
        if self.action in ("create", "create_conversion", "update", "partial_update", "destroy"):
            return [IsAdminOrStorekeeper()]
        return [IsAuthenticated()]
```

Pattern tương tự cho UnitConversionViewSet: Write = IsAdminOrStorekeeper.

## 3. Custom Permissions

Không cần — `IsAdmin`, `IsAdminOrStorekeeper`, `IsAuthenticated` đã đủ.

## 4. JWT Claims

Không áp dụng.
