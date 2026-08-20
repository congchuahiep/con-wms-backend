# Implementation Checklist — Site (Công Trường)

## Cấu hình

- [ ] Tạo app `sites` (`python manage.py startapp sites`) + thêm vào `INSTALLED_APPS` trong `config/settings.py`
- [ ] Đảm bảo không trùng `django.contrib.sites` (chưa cài — kiểm tra INSTALLED_APPS)

## Model

- [ ] `sites/models.py`: `Site` — `code` (unique), `name`, `manager`, `phone`, `address`, `note`, `is_active`, `created_at`, `updated_at`; `db_table="site"`, `__str__ = "code — name"`
- [ ] `makemigrations sites` + `migrate`

## Serializers / Views / Filters / URLs

- [ ] `sites/serializers.py`: `SiteSerializer` (fields: id, code, name, manager, phone, address, note, isActive, createdAt, updatedAt; validate code unique — server 400)
- [ ] `sites/views.py`: `SiteViewSet(ModelViewSet)` — queryset `filter(is_active=True)`, write `IsAdmin`, read `IsAuthenticated`, search code/name, không phân trang
- [ ] `sites/urls.py`: router prefix `sites` → `/api/sites/`
- [ ] `sites/admin.py`: đăng ký Site

## Tests (`sites/tests.py`)

- [ ] CRUD: tạo/sửa/xem/vô hiệu hóa hoạt động
- [ ] `code` trùng → 400
- [ ] Permission: thủ kho/kế toán POST → 403; GET → 200
- [ ] Soft delete: DELETE → `is_active=false`, không xuất hiện ở list mặc định; `?is_active=false` thấy
- [ ] Search theo code/name

## Seed

- [ ] `sites/management/commands/seed_sites.py`: 2-3 công trường mẫu (CT_RG, CT_KE_SONG_BE...)

## Tài liệu

- [ ] Check off các mục trên sau khi code (mỗi mục xong → `[x]`)
- [ ] Cập nhật `docs/entities/README.md` — trạng thái Site
