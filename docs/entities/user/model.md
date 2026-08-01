# Model — User

> Django app: `iam`
> Kế thừa: `AbstractUser`
> Auth field: `email` (username-less)

## 1. Thuộc tính

| # | Field | Kiểu | Ràng buộc | Ghi chú |
|---|---|---|---|---|
| 1 | `id` | BigAutoField (PK) | | Django mặc định |
| 2 | `email` | EmailField(255) | unique, required | Dùng làm USERNAME_FIELD |
| 3 | `password` | CharField(128) | required | Hash tự động |
| 4 | `first_name` | CharField(150) | optional | |
| 5 | `last_name` | CharField(150) | optional | |
| 6 | `phone` | CharField(15) | blank=True | SĐT liên lạc |
| 7 | `role` | CharField(30) | choices, required, default=storekeeper | Xem bảng role bên dưới |
| 8 | `is_active` | BooleanField | default=True | Khoá/mở tài khoản |
| 9 | `date_joined` | DateTimeField | auto_now_add | Django mặc định (AbstractUser) |
| 10 | `last_login` | DateTimeField | auto | Django mặc định (AbstractUser) |

> **Đã loại bỏ:** `username` (set `None`), dùng `email` làm định danh duy nhất.

## 2. Role (Vai trò)

| Key | Label (tiếng Việt) | Mô tả quyền khái quát |
|---|---|---|
| `admin` | Quản trị viên | CRUD tất cả; tạo/khoá user; quản trị danh mục |
| `storekeeper` | Thủ kho | Tạo phiếu nhập/xuất/kiểm kê; điều chỉnh tồn sau kiểm kê; xem tồn |
| `supervisor` | Chủ nhiệm công trình | Xem tồn + lịch sử xuất cho công trình mình; đề xuất xuất vật tư |
| `accountant` | Kế toán | Xem toàn bộ phiếu nhập + lịch sử giao dịch NCC *(read-only)* |

## 3. Quan hệ

| Entity đích | Cardinality | Mô tả |
|---|---|---|
| `InboundNote` | 1 → N | Người lập phiếu nhập |
| `OutboundNote` | 1 → N | Người lập phiếu xuất |
| `StocktakeNote` | 1 → N | Người lập phiếu kiểm kê |
| `Warehouse` | M → N | *(optional)* Phân công thủ kho phụ trách kho. Bản đầu chưa dùng. |

## 4. Quyết định thiết kế

| # | Quyết định | Lý do |
|---|---|---|
| D1 | Kế thừa `AbstractUser` | Giữ toàn bộ field auth có sẵn của Django, chỉ thêm `phone` + `role` |
| D2 | Role dùng `TextChoices` | Đơn giản, không cần Group/Permission phức tạp (đủ dùng cho 10 người) |
| D3 | Email-based auth (`USERNAME_FIELD = "email"`) | Tiện hơn cho người dùng, không cần nhớ username riêng; email vừa là định danh vừa là kênh liên lạc |
| D4 | Custom `UserManager` với `create_user` / `create_superuser` | Chuẩn hóa email (`normalize_email`), đảm bảo `set_password` luôn được gọi |
| D5 | Giữ `first_name` + `last_name` | Linh hoạt hiển thị, giữ convention Django |
| D6 | Không có `avatar` | Quy mô nhỏ, không cần |
