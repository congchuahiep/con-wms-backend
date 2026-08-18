# Implementation Checklist — Stock (Sổ kho & Tồn kho)

> Pha 1 đi cùng InboundNote. Pha 2/3 khi có OutboundNote / StocktakeNote.

## Cấu hình

- [x] App `inventory` đã có sẵn (tạo cùng InboundNote): `INSTALLED_APPS` + migration

## Model — Phase 1

- [x] `inventory/models.py`: model `MovementType` (TextChoices — 6 loại)
- [x] `inventory/models.py`: model `StockMovement` (14 fields — bỏ 2 FK `outbound_note`/`stocktake_note` vì target model chưa tồn tại, thêm ở phase 2/3)
  - `material` FK PROTECT, `warehouse` FK PROTECT
  - `quantity` DecimalField(14, 3)
  - `unit_price` DecimalField(14, 2) null/blank
  - `movement_type` CharField(40) choices
  - `date` DateField
  - `inbound_note` FK PROTECT — phase 1 bắt buộc (required)
  - `lot` CharField(50) null/blank — chừa sẵn
  - `reversal_of` FK self PROTECT null
  - `reason` TextField blank
  - `created_by` FK → iam.User PROTECT
  - `created_at` DateTimeField auto_now_add — **không có** updated_at
- [x] `Meta`: `db_table`, `verbose_name`, indexes:
  - `(warehouse, material, date)` — query tồn + báo cáo kỳ
  - `(movement_type, date)` — lọc sổ kho
  - `(inbound_note)` — trace phiếu
- [x] Phase 1 constraint: `inbound_note` NOT NULL (sau này thay bằng CheckConstraint "đúng 1 nguồn" khi đủ 3 FK)
- [x] `__str__` method
- [x] `inventory/admin.py`: đăng ký `StockMovement` (read-only admin, không cho sửa tay)
- [x] `makemigrations inventory` + `migrate`

## Logic ghi sổ (BaseNote)

- [x] `inventory/models.py`: `BaseNote` (abstract) — vòng đời chung của mọi phiếu:
  - `post(user)`: check draft → hook `_build_post_movements(user)` sinh dòng sổ kho → set `status="posted"` (transaction.atomic)
  - `void(reason, user)`: check posted → hook `_build_void_movements(reason, user)` sinh dòng ngược dấu (`reversal_of`, `date=today`, `reason`) → set `voided_by/voided_at/void_reason/status` (transaction.atomic)
  - `is_draft` / `is_posted` / `is_voided` properties
- [x] `InboundNote(BaseNote)`: 2 hook riêng — `_build_post_movements` (`movement_type` theo note_type, +quantity, `unit_price` nếu purchase) và `_build_void_movements`
- [x] `inventory/services.py`: chỉ còn sinh số phiếu (`generate_inbound_note_number`)

## Serializers

- [x] `inventory/serializers.py`: `StockBalanceSerializer` (read-only)
  - `material`, `unit`, `warehouse` nested đơn giản
  - `quantity`, `last_purchase_price`, `stock_value`
- [x] `inventory/serializers.py`: `StockMovementSerializer` (read-only)
  - Nested `material`, `warehouse`, `inbound_note` `{id, number}`, `created_by` `{id, email}`
  - `movement_type_label` = `get_movement_type_display()`

## Views

- [x] `inventory/views.py`: `StockBalanceViewSet` (read-only, chỉ list)
  - `get_queryset`: aggregate `SUM(quantity)` group by `(warehouse, material)`, annotate last purchase price (Subquery dòng `inbound_purchase_from_supplier` mới nhất)
  - Không phân trang
  - Route thủ công `path("stock/", ...)` để tránh `stock/{pk}/` nuốt `stock/movements/`
  - `@extend_schema` tags=["Stock"]
- [x] `inventory/views.py`: `StockMovementViewSet(ReadOnlyModelViewSet)`
  - `queryset` filter `reversal_of__isnull=True` mặc định (originals_only), order `-date, -id`
  - Pagination `page_size=50`
  - Router prefix `stock/movements` → URL `/api/stock/movements/`
- [x] `inventory/filters.py`: `StockBalanceFilter` (warehouse, material, category, has_stock) + `StockMovementFilter` (material, warehouse, movement_type, date_from, date_to, inbound_note)

## URLs

- [x] `inventory/urls.py`: `/api/stock/` (list) + `/api/stock/movements/` (list/detail) + `/api/inbound-notes/`

## Permissions

- [x] Cả 2 ViewSet: `IsAuthenticated`, read-only (không method write)

## Tests

- [x] `inventory/tests.py` (13 tests stock — tổng 31 tests app):
  - GET `/api/stock/` unauthenticated → 401
  - Chốt phiếu nhập mua → tồn tăng đúng, `lastPurchasePrice` đúng, `stockValue` đúng
  - Chốt phiếu hoàn trả → tồn tăng, **không** ảnh hưởng `lastPurchasePrice`
  - Phiếu draft → không có dòng sổ kho, tồn không đổi
  - Hủy phiếu đã chốt → tồn trở về 0, dòng reversal có `reason` + `reversal_of`
  - Hủy phiếu thiếu lý do → 400
  - Sổ kho: filter theo material / movement_type / khoảng ngày
  - POST `/api/stock/movements/` → 405
  - GET sổ kho kế toán → 200 (xem được)
  - Trace: dòng sổ kho trỏ đúng `inbound_note`
- [x] Chạy `python manage.py test inventory` — 31/31 OK

## Seed Data

- [x] `inventory/management/commands/seed_stock.py`: sau khi seed 2 phiếu nhập mẫu → in tồn kho hiện tại
- [x] Chạy `python manage.py seed_stock` — tồn kho mẫu hiện đúng (XM: 110, Cát vàng: 5.5)

## Tài liệu

- [x] Cập nhật `docs/entities/README.md` — trạng thái Stock: ✅ Done
- [x] Cập nhật `docs/entities/stock/change-log.md` — checklist done
- [x] Tạo `docs/adr/0001-stock-movement-ledger.md` — ADR quyết định sổ kho vs bảng tồn

## Phase 2 (khi có OutboundNote)

- [ ] Thêm logic `post_outbound_note` / `void_outbound_note` (dòng −)
- [ ] Transfer: 1 dòng phiếu → 2 dòng sổ kho (`outbound_transfer_to_warehouse` kho đi, `inbound_transfer_from_warehouse` kho đến)
- [ ] Bổ sung CheckConstraint "đúng 1 nguồn" với 2 FK

## Phase 3 (khi có StocktakeNote)

- [ ] Thêm logic chốt kiểm kê → dòng `stocktake_adjustment` (chênh lệch ±, kèm lý do hư/mất/sai số/thừa)
- [ ] CheckConstraint đầy đủ 3 FK
