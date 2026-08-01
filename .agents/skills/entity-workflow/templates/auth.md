# Authentication & Authorization — {{ENTITY_NAME}}

## 1. Permissions

| Endpoint | Permission Class | Ghi chú |
|---|---|---|
| `GET /api/{{prefix}}/` | `IsAuthenticated` | Mọi role đã đăng nhập |
| `POST /api/{{prefix}}/` | `{{WRITE_PERMISSION}}` | |
| `PUT /api/{{prefix}}/{id}/` | `{{WRITE_PERMISSION}}` | |
| `DELETE /api/{{prefix}}/{id}/` | `{{DELETE_PERMISSION}}` | |

## 2. Custom Permissions (nếu cần)

```python
# {{DJANGO_APP}}/permissions.py
from rest_framework.permissions import BasePermission

class {{PERMISSION_NAME}}(BasePermission):
    def has_permission(self, request, view):
        # TODO: logic kiểm tra quyền
        pass
```

## 3. JWT Claims (nếu entity cần nhúng vào token)

Không áp dụng / hoặc mô tả claim cần thêm.
