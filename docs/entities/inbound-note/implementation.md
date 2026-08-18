# Implementation Checklist — Inbound Note

> Làm cùng lúc với entity [`Stock`](../stock/implementation.md) — chốt/hủy phiếu ghi sổ kho.

## Cấu hình

- [x] Tạo Django app: `python manage.py startapp inventory`
- [x] Thêm `"inventory"` vào `INSTALLED_APPS` trong `config/settings.py`

## Model

- [x] `inventory/models.py`: model `NoteType` (TextChoices: purchase/return)
- [x] `inventory/models.py`: model `NoteStatus` (TextChoices: draft/posted/voided)
- [x] `inventory/models.py`: model `InboundNote` (14 fields)
  - `number` CharField(30) unique
  - `note_type` CharField(20) choices, default=purchase
  - `status` CharField(20) choices, default=draft
  - `date` DateField default=timezone.localdate
  - `warehouse` FK → Warehouse PROTECT
  - `supplier` FK → Supplier PROTECT null/blank
  - `created_by` FK → iam.User PROTECT
  - `voided_by` FK → iam.User PROTECT null/blank
  - `voided_at` DateTimeField null/blank
  - `void_reason` TextField blank
  - `note` TextField blank
  - `created_at`, `updated_at` DateTimeField auto
- [x] `inventory/models.py`: model `InboundNoteLine` (9 fields)
  - `inbound_note` FK → InboundNote CASCADE related_name="lines"
  - `material` FK → Material PROTECT
  - `quantity` DecimalField(14, 3)
  - `unit_price` DecimalField(14, 2)
  - `line_no` IntegerField default=0
  - `note` TextField blank
  - `created_at`, `updated_at` DateTimeField auto
- [x] `__str__` methods
- [x] `Meta`: `db_table`, `verbose_name`, indexes (warehouse, supplier, date, note_type, status)
- [x] `inventory/admin.py`: đăng ký 2 model (TabularInline cho lines)
- [x] Chạy `python manage.py makemigrations inventory` + `migrate`

## Serializers

- [x] `inventory/serializers.py`: `InboundNoteLineSerializer`
  - `material_id` PrimaryKeyRelatedField write_only (source="material")
  - `material` SimpleMaterialSerializer read_only
  - Validate: quantity > 0, unit_price >= 0
- [x] `inventory/serializers.py`: `InboundNoteSerializer`
  - `warehouse_id` / `supplier_id` write_only, nested read_only output
  - `lines` nested InboundNoteLineSerializer (many=True)
  - `number`, `status`, `voided_by`, `voided_at` read_only
  - `total_amount` SerializerMethodField = Σ(quantity × unit_price)
  - Validate: purchase→supplier required, return→supplier null, ≥1 line
  - `create()` + `update()` với `transaction.atomic`, set line_no, replace-all lines khi update (chỉ draft)
- [x] `inventory/serializers.py`: `VoidInboundNoteSerializer` — `reason` required
- [x] `inventory/serializers.py`: `SimpleWarehouseSerializer`, `SimpleSupplierSerializer`, `SimpleMaterialSerializer`, `SimpleUserSerializer` (output)

## Logic nghiệp vụ

- [x] `inventory/models.py`: `BaseNote.post()` — chốt phiếu (xem [`stock/implementation.md`](../stock/implementation.md)):
  - Hook `_build_post_movements(user)` của `InboundNote` tạo `StockMovement` cho từng dòng (+quantity, unit_price nếu purchase, date=note.date)
  - `transaction.atomic` + set `status="posted"`
- [x] `inventory/models.py`: `BaseNote.void()`:
  - Hook `_build_void_movements(reason, user)` tạo dòng sổ kho ngược dấu (`reversal_of` trỏ dòng gốc, date=today, reason)
  - `transaction.atomic` + set `status="voided"`, `voided_by`, `voided_at`, `void_reason`

## Views

- [x] `inventory/views.py`: `InboundNoteViewSet(ModelViewSet)`
  - `get_queryset`: `select_related("warehouse", "supplier", "created_by", "voided_by").prefetch_related("lines__material").order_by("-date", "-id")`
  - `perform_create`: set `created_by=request.user`, generate `number`
  - `destroy`: chỉ khi draft → xóa cứng; posted/voided → 400
  - `update`/`partial_update`: chỉ khi draft; posted/voided → 400
  - `@action post`: gọi `note.post(request.user)`
  - `@action void`: validate `reason`, gọi `note.void(reason, request.user)`
  - `@extend_schema` + `@extend_schema_view` tags=["InboundNote"]
  - Pagination: PageNumberPagination page_size=20
- [x] `inventory/filters.py`: `InboundNoteFilter(FilterSet)` — note_type, status, warehouse, supplier, date_from, date_to, search

## URLs

- [x] `inventory/urls.py`: `DefaultRouter` register `inbound-notes` với `InboundNoteViewSet`
- [x] Include vào `config/urls.py`: `path("api/", include("inventory.urls"))` → URL cuối: `/api/inbound-notes/`

## Permissions

- [x] Không cần file `inventory/permissions.py` mới — dùng lại `iam.permissions`
- [x] Import: `from iam.permissions import IsAdmin, IsAdminOrStorekeeper`

## Tests

- [x] `inventory/tests.py`: 31 tests — all pass
  - GET list unauthenticated → 401
  - GET list storekeeper → 200
  - POST storekeeper (purchase + supplier) → 201, number format đúng, status=draft
  - POST accountant → 403
  - POST purchase thiếu supplier → 400
  - POST return có supplier → 400
  - POST không có lines → 400
  - POST quantity=0 → 400
  - POST unit_price âm → 400
  - GET detail → 200 kèm lines + total_amount
  - PUT draft → 200, lines replace-all; PUT posted → 400
  - POST /post/ draft → 200, status=posted, **dòng sổ kho được tạo** (StockMovement count = số dòng)
  - POST /post/ lần 2 → 400
  - POST /void/ posted thiếu reason → 400
  - POST /void/ posted có reason → 200, status=voided, **dòng sổ kho ngược dấu được tạo**
  - DELETE draft → 204; DELETE posted → 400
  - Số phiếu tăng dần trong ngày (001 → 002)
- [x] Chạy `python manage.py test inventory` — 31/31 OK

## Seed Data

- [x] `inventory/management/commands/seed_inbound_notes.py`: 2 phiếu mẫu (1 purchase + 1 return) → tự chốt (status=posted + dòng sổ kho)

| number | type | warehouse | supplier | lines |
|---|---|---|---|---|
| `PN-20260801-001` | purchase | KHO_CHINH | NCC001 | 2 dòng (xi măng 100 bao × 88,000đ; cát 5.5 m³ × 350,000đ) |
| `PN-20260802-001` | return_from_site | KHO_CHINH | — | 1 dòng (xi măng công trường trả lại 10 bao × 88,000đ) |

- [x] Chạy `python manage.py seed_inbound_notes` — 2 phiếu đã tạo + đã chốt

## Tài liệu

- [x] Cập nhật `docs/entities/README.md` — trạng thái Inbound Note: ✅ Done
- [x] Cập nhật `docs/entities/inbound-note/change-log.md` — checklist done
