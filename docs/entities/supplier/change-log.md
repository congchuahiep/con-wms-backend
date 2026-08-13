# Change Log — Supplier

## v1.0 — 2026-08-12

Khởi tạo thiết kế ban đầu:

- 12 fields: code, name, tax_code, contact_person, phone, email, address, note, is_active, created_at, updated_at
- 5 API endpoints REST chuẩn (CRUD + soft delete)
- Permission: Read → IsAuthenticated, Write → IsAdmin
- Pattern theo Warehouse — CRUD data master đơn giản
- `tax_code` unique=True, blank=True — mỗi NCC có MST duy nhất, blank cho NCC chưa có MST

### Kết quả validate Context7

| Library | Kết quả |
|---|---|
| Django 6.0 | ✅ BigAutoField, CharField unique, EmailField, BooleanField default, DateTimeField auto — tất cả chuẩn |
| DRF | ✅ ModelViewSet, ModelSerializer, DefaultRouter, SearchFilter, DjangoFilterBackend — đúng best practice |

### Triển khai (2026-08-12)

- ✅ Tạo app `supplier`, model 12 fields, migration OK
- ✅ CRUD ViewSet + filters + drf-spectacular schema
- ✅ 8 tests — 8/8 pass
- ✅ Seed 2 NCC mẫu
- ✅ Cập nhật `docs/entities/README.md` + `config/settings.py` + `config/urls.py`
