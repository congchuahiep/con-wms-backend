# Implementation Checklist — User

Danh sách các bước triển khai Django app `iam`.

## Cấu hình

- [x] Tạo Django app: `python manage.py startapp iam`
- [x] Thêm `"iam"` vào `INSTALLED_APPS`
- [x] Thêm `"rest_framework_simplejwt.token_blacklist"` vào `INSTALLED_APPS`
- [x] `AUTH_USER_MODEL = "iam.User"` trước migration đầu tiên
- [x] `SIMPLE_JWT` dict (8h access, 7d refresh, rotate, blacklist)

## Model

- [x] `iam/models.py`: `AbstractUser`, `username = None`, `USERNAME_FIELD = "email"`
- [x] `iam/models.py`: custom `UserManager` với `create_user` / `create_superuser` + `normalize_email`
- [x] `iam/models.py`: `Role(TextChoices)` — admin, storekeeper, supervisor, accountant
- [x] `iam/admin.py`: `UserAdmin` custom hiển thị `phone` + `role`
- [x] `python manage.py makemigrations iam` + `migrate`

## Serializers

- [x] `UserProfileSerializer` — fields: id, email, first_name, last_name, phone, role
- [x] `LoginSerializer(TokenObtainPairSerializer)` — nhúng `email` + `role` vào JWT claim
- [x] `RegisterSerializer` — tạo user qua `User.objects.create_user()` (có normalize email)
- [x] `LogoutSerializer` — validate `refresh` token

## Permissions

- [x] `IsAdmin`, `IsStorekeeper`, `IsAdminOrStorekeeper`, `IsAdminOrAccountant`, `IsAdminOrSupervisor`

## Views

- [x] `AuthViewSet(GenericViewSet)` + `@extend_schema` (drf_spectacular)
- [x] `login`, `register`, `refresh` → `AllowAny`
- [x] `logout`, `me` → `IsAuthenticated` + JWT
- [x] `register` trả về token + user profile

## URLs

- [x] `DefaultRouter` register `auth` + include tại `api/`
- [x] `config/urls.py`: schema + swagger (drf_spectacular)

## Seed Data

- [x] `python manage.py seed_users` — 4 user, password `Password123!`

| Email                | Role        |
| -------------------- | ----------- |
| `admin@gmail.com`    | admin       |
| `thukho@gmail.com`   | storekeeper |
| `chunhiem@gmail.com` | supervisor  |
| `ketoan@gmail.com`   | accountant  |

## Tests

- [ ] `iam/tests.py`: test login, register, refresh, logout, me
- [ ] Test permissions: storekeeper không truy cập được endpoint admin
