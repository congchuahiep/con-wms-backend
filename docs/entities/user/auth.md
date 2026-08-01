# Authentication & Authorization — User

## 1. JWT Configuration (`SIMPLE_JWT`)

Cấu hình trong `config/settings.py`:

```python
from datetime import timedelta

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=8),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "TOKEN_OBTAIN_SERIALIZER": "iam.serializers.LoginSerializer",
}
```

| Tham số | Giá trị | Lý do |
|---|---|---|
| `ACCESS_TOKEN_LIFETIME` | 8 giờ | Bằng 1 ca làm việc |
| `REFRESH_TOKEN_LIFETIME` | 7 ngày | Đăng nhập lại mỗi tuần |
| `ROTATE_REFRESH_TOKENS` | `True` | Mỗi lần refresh cấp refresh mới → tăng bảo mật |
| `BLACKLIST_AFTER_ROTATION` | `True` | Refresh cũ bị vô hiệu ngay khi rotate |
| `UPDATE_LAST_LOGIN` | `True` | Cập nhật `last_login` mỗi lần refresh |
| `TOKEN_OBTAIN_SERIALIZER` | `iam.serializers.LoginSerializer` | Nhúng `email` + `role` vào JWT claim |

## 2. Custom Token Serializer

File: `iam/serializers.py`

```python
class LoginSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["email"] = user.email
        token["role"] = user.role
        return token
```

**Mục đích:** `email` + `role` được nhúng vào JWT payload → frontend đọc trực tiếp từ token, khỏi gọi `/api/auth/me/`.

## 3. Custom Permissions

File: `iam/permissions.py`

```python
from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "admin"

class IsStorekeeper(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "storekeeper"

class IsAdminOrStorekeeper(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ("admin", "storekeeper")

class IsAdminOrAccountant(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ("admin", "accountant")

class IsAdminOrSupervisor(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ("admin", "supervisor")
```

| Permission Class | Sử dụng cho endpoint |
|---|---|
| `IsAdmin` | `POST/PUT/DELETE` user, danh mục |
| `IsStorekeeper` | Tạo phiếu nhập/xuất/kiểm kê |
| `IsAdminOrStorekeeper` | Điều chỉnh tồn, duyệt kiểm kê |
| `IsAdminOrAccountant` | Xem phiếu nhập, lịch sử NCC |
| `IsAdminOrSupervisor` | Xem tồn, đề xuất xuất |

> **Nguyên tắc:** Read-only (GET) chung cho mọi role. Write dùng permission tương ứng. Tất cả kế thừa `IsAuthenticated` ở `DEFAULT_PERMISSION_CLASSES`.

## 4. Token Blacklist (Logout)

Đã thêm `"rest_framework_simplejwt.token_blacklist"` vào `INSTALLED_APPS`.

Logout flow: `POST /api/auth/logout/` + `{"refresh": "..."}` → token bị blacklist → không dùng lại được.

## 5. ViewSet Pattern

Auth endpoints được gom vào `AuthViewSet(GenericViewSet)`:

```python
class AuthViewSet(viewsets.GenericViewSet):
    def get_permissions(self):
        if self.action in ("login", "refresh", "register"):
            return [AllowAny()]
        return [IsAuthenticated()]

    @action(detail=False, methods=["post"], url_path="login")
    def login(self, request): ...

    @action(detail=False, methods=["post"], url_path="register")
    def register(self, request): ...

    @action(detail=False, methods=["post"], url_path="refresh")
    def refresh(self, request): ...

    @action(detail=False, methods=["post"], url_path="logout")
    def logout(self, request): ...

    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request): ...
```

Router: `DefaultRouter` register prefix `auth` → include tại `api/` → URL cuối: `/api/auth/{action}/`.
