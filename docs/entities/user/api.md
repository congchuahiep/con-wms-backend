# API Endpoints — User

## Danh sách endpoint

| Method | Endpoint              | Mô tả                         | Auth     | Request Body                                                                   | Response                                                                                            |
| ------ | --------------------- | ----------------------------- | -------- | ------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------- |
| `POST` | `/api/auth/login/`    | Đăng nhập                     | AllowAny | `{"email": "...", "password": "..."}`                                          | `{"access": "...", "refresh": "..."}`                                                               |
| `POST` | `/api/auth/register/` | Đăng ký tài khoản             | AllowAny | `{"email": "...", "password": "...", "first_name": "...", "last_name": "..."}` | `{"user": {...}, "access": "...", "refresh": "..."}`                                                |
| `POST` | `/api/auth/refresh/`  | Làm mới access token          | AllowAny | `{"refresh": "..."}`                                                           | `{"access": "..."}`                                                                                 |
| `POST` | `/api/auth/logout/`   | Đăng xuất (blacklist refresh) | JWT      | `{"refresh": "..."}`                                                           | `204 No Content`                                                                                    |
| `GET`  | `/api/auth/me/`       | Thông tin user hiện tại       | JWT      | —                                                                              | `{"id": 1, "email": "...", "first_name": "...", "last_name": "...", "phone": "...", "role": "..."}` |

## Ghi chú

- **Login** chỉ trả về token (`access` + `refresh`). Muốn lấy profile → gọi `GET /api/auth/me/`.
- **Register** trả về cả token lẫn user profile để frontend khởi tạo state ngay, không cần gọi thêm API.
- Logout chỉ cần gửi refresh token — access token tự hết hạn sau 8h.
- Tất cả endpoint public (`login`, `register`, `refresh`) có `@extend_schema(auth=[])` để drf_spectacular không yêu cầu auth trong Swagger UI.
