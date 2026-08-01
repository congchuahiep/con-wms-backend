# Change Log — User Entity

## v1.2 — 2026-08-01

Refactor sau triển khai thực tế:

| #   | Thay đổi                                                                        | Lý do                                                                  |
| --- | ------------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| 1   | Chuyển sang email-based auth (`username = None`, `USERNAME_FIELD = "email"`)    | Tiện hơn cho người dùng cuối, không cần nhớ username riêng             |
| 2   | Custom `UserManager` với `create_user` / `create_superuser` + `normalize_email` | Chuẩn hóa email khi đăng ký, tránh trùng lặp do case-sensitive         |
| 3   | Refactor views sang `AuthViewSet(GenericViewSet)` + `@action`                   | Đồng nhất ViewSet pattern với các entity sau; hỗ trợ `drf_spectacular` |
| 4   | Thêm endpoint `POST /api/auth/register/`                                        | Cho phép tự đăng ký tài khoản, trả về token + profile                  |
| 5   | Tách `LogoutSerializer`, `RegisterSerializer`, `UserProfileSerializer`          | Mỗi serializer 1 trách nhiệm, sạch hơn                                 |
| 6   | Chỉnh `LoginSerializer` claim: `email` thay `username`                          | Khớp với model email-based                                             |
| 7   | URL prefix đổi từ `api/auth/` → `api/` (router tự thêm `auth/`)                 | Tránh double prefix khi dùng DefaultRouter                             |
| 8   | Thêm `@extend_schema(auth=[])` cho public endpoint                              | Swagger UI không yêu cầu auth cho login/register/refresh               |
| 9   | Thêm dev deps (django-stubs, ruff)                                              | Type checking + lint cho codebase                                      |

## v1.1 — 2026-08-01

Bổ sung 5 mục sau khi tham chiếu tài liệu chính thức (Django 6.0, simplejwt, DRF):

| #   | Thay đổi                                                 | Lý do                                                       |
| --- | -------------------------------------------------------- | ----------------------------------------------------------- |
| 1   | Thêm `SIMPLE_JWT` settings chi tiết                      | Docs simplejwt yêu cầu cấu hình dict + serializer tuỳ chỉnh |
| 2   | Thêm `LoginSerializer` custom nhúng `role` vào JWT claim | Docs simplejwt khuyến nghị custom `get_token()`             |
| 3   | Thêm endpoint `POST /api/auth/logout/` (token blacklist) | Docs simplejwt có sẵn `TokenBlacklistView`                  |
| 4   | Thêm 5 class `BasePermission` theo role                  | Docs DRF khuyến nghị override `has_permission()`            |
| 5   | Thêm `UserAdmin` checklist + `AUTH_USER_MODEL`           | Docs Django bắt buộc đăng ký custom admin                   |

## v1.0 — 2026-08-01

Khởi tạo: `AbstractUser`, 4 role, giữ `first_name`/`last_name`, không `avatar`.
