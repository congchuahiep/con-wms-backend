# Authentication & Authorization — Unit + UnitConversion

## 1. Permissions

Dùng lại từ `iam.permissions`.

| Endpoint                                         | Permission        | Ghi chú |
| ------------------------------------------------ | ----------------- | ------- |
| `GET /api/units/`, `GET /api/units/{id}/`        | `IsAuthenticated` | Mọi role đều xem được |
| `GET /api/units/{id}/conversions/`               | `IsAuthenticated` | Mọi role đều xem được |
| `POST/PUT/PATCH/DELETE` — Unit                   | `IsAdmin`         | **Thắt chặt**: trước đây là IsAdminOrStorekeeper |
| `POST /api/units/{id}/conversions/`              | `IsAdmin`         | **Thắt chặt** |
| `PUT/DELETE /api/unit-conversions/{id}/`         | `IsAdmin`         | Giữ nguyên |

### Tại sao thắt chặt về IsAdmin?

Trước đây Thủ kho được toàn quyền catalog để tránh block workflow nhập kho.
Tuy nhiên với `conversion_type`, việc thêm/sửa Unit và UnitConversion đòi hỏi
hiểu đúng domain (global vs material). Sai sót có thể làm hỏng logic quy đổi
toàn hệ thống. Chỉ Admin mới nên thao tác.

> **Có thể cân nhắc giữ IsAdminOrStorekeeper nếu công ty vẫn muốn Thủ kho toàn quyền.**
> Đây là quyết định nghiệp vụ, không phải kỹ thuật.

## 2. ViewSet permission mapping

```python
class UnitViewSet(viewsets.ModelViewSet):
    def get_permissions(self):
        if self.action in (
            "create", "update", "partial_update", "destroy",
            "create_conversion",
        ):
            return [IsAdmin()]
        return [IsAuthenticated()]


class UnitConversionViewSet(mixins.UpdateModelMixin, mixins.DestroyModelMixin,
                             viewsets.GenericViewSet):
    def get_permissions(self):
        return [IsAdmin()]
```

## 3. Custom Permissions

Không cần.
