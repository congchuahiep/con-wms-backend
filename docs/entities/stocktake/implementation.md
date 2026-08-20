# Implementation Checklist — Stocktake Note

> Phase 3 của Stock (sổ kho). Đi cùng: thêm `stocktake_note` FK + CheckConstraint "đúng 1 nguồn" đủ 3 FK vào `StockMovement` (xem [`../stock/implementation.md`](../stock/implementation.md)).

## Model

- [ ] `inventory/models.py`: `StocktakeNote(BaseNote)`:
  - [ ] Không có field riêng ngoài base (không `note_type` — D8)
  - [ ] `Meta(BaseNote.Meta)`: `db_table="stocktake_note"`, verbose "Phiếu kiểm kê"
- [ ] `inventory/models.py`: `StocktakeLine`:
  - [ ] `stocktake_note` FK CASCADE `related_name="lines"`, `material` FK PROTECT
  - [ ] `difference` Decimal(14,3) required — chênh lệch có dấu (±), ≠ 0
  - [ ] `reason` TextField blank — bắt buộc khi chốt (difference ≠ 0 luôn nên lúc nào cũng cần)
  - [ ] `line_no`, `note`, timestamps
  - [ ] **Không** có `book_quantity` / `counted_quantity` (D1)
- [ ] Hooks:
  - [ ] `_build_post_movements`: check `difference ≥ −tồn hiện tại` (tồn tính lại lúc chốt — aggregate `Sum` theo warehouse+material) → check `reason` → 1 dòng `stocktake_adjustment` (`quantity = difference`, `reason`)
  - [ ] `_build_void_movements`: đảo dấu mọi dòng gốc
- [ ] `inventory/services.py`: `generate_stocktake_note_number` (`PK-YYYYMMDD-NNN`)
- [ ] `inventory/models.py` `StockMovement`: thêm `stocktake_note` FK (null) + index `ix_sm_stocktake_note` + CheckConstraint "đúng 1 nguồn" đủ 3 FK + CheckConstraint `unit_price` ⇔ `inbound_purchase_from_supplier`
- [ ] `makemigrations inventory` + `migrate`

## Serializers

- [ ] `inventory/serializers.py`: `StocktakeLineSerializer` (material_id write / material read, difference, reason — không có book/counted)
- [ ] `inventory/serializers.py`: `StocktakeNoteSerializer`:
  - [ ] Validate: ≥ 1 dòng; `difference` bắt buộc, ≠ 0
  - [ ] `total_quantity` = số dòng
  - [ ] Nested write + replace-all update (giống các phiếu khác)
- [ ] `inventory/serializers.py`: `StocktakeNoteListSerializer` (list gọn — không lines)
- [ ] `inventory/serializers.py`: `VoidStocktakeNoteSerializer` (reason required)
- [ ] `inventory/serializers.py`: `SimpleStocktakeNoteSerializer` (`{id, number}`) cho `StockMovementSerializer`
- [ ] `StockMovementSerializer`: thêm `stocktake_note` (nullable)

## Views / Filters / URLs

- [ ] `inventory/views.py`: `StocktakeNoteViewSet` (giống InboundNoteViewSet: chỉ draft mới update/destroy, `@action post` → `note.post(user)`, `@action void` → `note.void(reason, user)`)
- [ ] `inventory/filters.py`: `StocktakeNoteFilter` — status, warehouse, date_from, date_to
- [ ] `inventory/urls.py`: register prefix `stocktake-notes`

## Permissions

- [ ] Đọc `IsAuthenticated`; ghi/chốt/hủy `IsAdminOrStorekeeper` (giống các Note khác)

## Tests (`inventory/tests.py`)

- [ ] Tạo phiếu kèm lines difference → 201; chốt → 1 dòng `stocktake_adjustment`/dòng phiếu (dương/âm đúng)
- [ ] Chốt khi `difference` làm tồn âm (|âm| > tồn hiện tại) → 400
- [ ] Chốt thiếu `reason` → 400
- [ ] Dòng `difference = 0` → 400
- [ ] Tạo phiếu không dòng → 400
- [ ] Hủy phiếu kiểm kê → đảo dấu dòng điều chỉnh, tồn về trước kiểm kê
- [ ] PUT/DELETE phiếu đã chốt → 400; `/void/` thiếu reason → 400
- [ ] Permission: kế toán tạo → 403, xem → 200
- [ ] Filter status / warehouse / date

## Seed

- [ ] `inventory/management/commands/seed_stocktake_notes.py`: 1 phiếu kiểm kê (vài dòng lệch ± kèm reason) — xác nhận tồn sau kiểm kê khớp số đếm

## Tài liệu

- [ ] Check off các mục trên sau khi code (mỗi mục xong → `[x]`)
- [ ] Cập nhật `docs/entities/README.md` — trạng thái Stocktake