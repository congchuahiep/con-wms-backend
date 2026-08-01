# Implementation Checklist — {{ENTITY_NAME}}

## Cấu hình

- [ ] Tạo Django app: `python manage.py startapp {{DJANGO_APP}}`
- [ ] Thêm `"{{DJANGO_APP}}"` vào `INSTALLED_APPS`

## Model

- [ ] `{{DJANGO_APP}}/models.py`: định nghĩa model + enums
- [ ] `{{DJANGO_APP}}/admin.py`: đăng ký model với Admin
- [ ] Chạy `python manage.py makemigrations {{DJANGO_APP}}` + `migrate`

## Serializers

- [ ] `{{DJANGO_APP}}/serializers.py`: serializer cho list/detail/create/update

## Views

- [ ] `{{DJANGO_APP}}/views.py`: ViewSet hoặc APIView
- [ ] `{{DJANGO_APP}}/filters.py`: filterset (nếu cần)

## URLs

- [ ] `{{DJANGO_APP}}/urls.py`: route với DefaultRouter hoặc path()
- [ ] Include vào `config/urls.py` dưới prefix `/api/{{prefix}}/`

## Permissions

- [ ] Gán `permission_classes` cho từng view
- [ ] `{{DJANGO_APP}}/permissions.py`: custom permission (nếu có)

## Tests

- [ ] `{{DJANGO_APP}}/tests.py`: test CRUD + permissions
- [ ] Chạy `python manage.py test {{DJANGO_APP}}`

## Seed Data

- [ ] `{{DJANGO_APP}}/management/commands/seed_{{DJANGO_APP}}.py`: data mẫu
