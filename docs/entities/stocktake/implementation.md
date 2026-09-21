# Implementation Checklist — Stocktake Note

> Phase 3 của Stock (sổ kho). Đi cùng: thêm `stocktake_note` FK + CheckConstraint "đúng 1 nguồn" đủ 3 FK vào `StockMovement` (xem [`../stock/implementation.md`](../stock/implementation.md)).

## Model

- [x] `inventory/models.py`: `StocktakeNote(BaseNote)`:
  - [x] Không có field riêng ngoài base (không `note_type` — D8)
  - [x] `Meta(BaseNote.Meta)`: `db_table="stocktake_note"`, verbose "Phiếu kiểm kê"
- [x] `inventory/models.py`: `StocktakeLine`:
  - [x] `stocktake_note` FK CASCADE `related_name="lines"`, `material` FK PROTECT
  - [x] `difference` Decimal(14,3) required — chênh lệch có dấu (±), ≠ 0
  - [x] `reason` TextField blank — bắt buộc khi chốt (difference ≠ 0 luôn nên lúc nào cũng cần)
  - [x] `line_no`, `note`, timestamps
  - [x] **Không** có `book_quantity` / `counted_quantity` (D1)
- [x] Hooks:
  - [x] `_build_post_movements`: check `difference ≥ −tồn hiện tại` (tồn tính lại lúc chốt — aggregate `Sum` theo warehouse+material) → check `reason` → 1 dòng `stocktake_adjustment` (`quantity = difference`, `reason`)
  - [x] `_build_void_movements`: đảo dấu mọi dòng gốc
- [x] `inventory/services.py`: `generate_stocktake_note_number` (`PK-YYYYMMDD-NNN`)
- [x] `inventory/models.py` `StockMovement`: thêm `stocktake_note` FK (null) + index `ix_sm_stocktake_note` + CheckConstraint "đúng 1 nguồn" đủ 3 FK + CheckConstraint `unit_price` ⇔ `inbound_purchase_from_supplier`
- [x] `makemigrations inventory` + `migrate`

## Serializers

- [x] `inventory/serializers.py`: `StocktakeLineSerializer` (material_id write / material read, difference, reason — không có book/counted)
- [x] `inventory/serializers.py`: `StocktakeNoteSerializer`:
  - [x] Validate: ≥ 1 dòng; `difference` bắt buộc, ≠ 0
  - [x] `total_quantity` = số dòng
  - [x] Nested write + replace-all update (giống các phiếu khác)
- [x] `inventory/serializers.py`: `StocktakeNoteListSerializer` (list gọn — không lines)
- [x] `inventory/serializers.py`: `VoidStocktakeNoteSerializer` (reason required)
- [x] `inventory/serializers.py`: `SimpleStocktakeNoteSerializer` (`{id, number}`) cho `StockMovementSerializer`
- [x] `StockMovementSerializer`: thêm `stocktake_note` (nullable)

## Views / Filters / URLs

- [x] `inventory/views.py`: `StocktakeNoteViewSet` (giống InboundNoteViewSet: chỉ draft mới update/destroy, `@action post` → `note.post(user)`, `@action void` → `note.void(reason, user)`)
- [x] `inventory/filters.py`: `StocktakeNoteFilter` — status, warehouse, date_from, date_to
- [x] `inventory/urls.py`: register prefix `stocktake-notes`

## Permissions

- [x] Đọc `IsAuthenticated`; ghi/chốt/hủy `IsAdminOrStorekeeper` (giống các Note khác)

## Tests (`inventory/tests.py`)

- [x] Tạo phiếu kèm lines difference → 201; chốt → 1 dòng `stocktake_adjustment`/dòng phiếu (dương/âm đúng)
- [x] Chốt khi `difference` làm tồn âm (|âm| > tồn hiện tại) → 400
- [x] Chốt thiếu `reason` → 400
- [x] Dòng `difference = 0` → 400
- [x] Tạo phiếu không dòng → 400
- [x] Hủy phiếu kiểm kê → đảo dấu dòng điều chỉnh, tồn về trước kiểm kê
- [x] PUT/DELETE phiếu đã chốt → 400; `/void/` thiếu reason → 400
- [x] Permission: kế toán tạo → 403, xem → 200
- [x] Filter status / warehouse / date

## Seed

- [x] `inventory/management/commands/seed_stocktake_notes.py`: 1 phiếu kiểm kê (vài dòng lệch ± kèm reason) — xác nhận tồn sau kiểm kê khớp số đếm

## Tài liệu

- [x] Check off các mục trên sau khi code (mỗi mục xong → `[x]`)
- [x] Cập nhật `docs/entities/README.md` — trạng thái Stocktake