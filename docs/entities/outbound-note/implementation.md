# Implementation Checklist — Outbound Note

> Phase 2 của Stock (sổ kho). Đi cùng: thêm `outbound_note` FK + CheckConstraint "đúng 1 nguồn" vào `StockMovement` (xem [`../stock/implementation.md`](../stock/implementation.md)).

## Model

- [ ] `inventory/models.py`: `OutboundNote(BaseNote)`:
  - [ ] `class Type(TextChoices)`: `ISSUE_FOR_USE` / `TRANSFER`
  - [ ] `note_type` CharField(20) choices, default=`issue_for_use`
  - [ ] `to_warehouse` FK → Warehouse (PROTECT, null/blank) — kho đích khi transfer
  - [ ] `site` FK → Site (PROTECT, null/blank) — công trường nhận hàng khi issue_for_use
  - [ ] `Meta(BaseNote.Meta)`: `db_table="outbound_note"`, verbose "Phiếu xuất", index `to_warehouse` + `site`
- [ ] `inventory/models.py`: `OutboundNoteLine`:
  - [ ] `outbound_note` FK CASCADE `related_name="lines"`, `material` FK PROTECT, `quantity` Decimal(14,3), `line_no`, `note`, timestamps
  - [ ] **Không có** `unit_price` (D5)
- [ ] Hooks:
  - [ ] `_build_post_movements`: check tồn đủ → `issue_for_use`: 1 dòng `outbound_issue_for_use` (−); `transfer`: 2 dòng `outbound_transfer_to_warehouse` (−, kho đi) + `inbound_transfer_from_warehouse` (+, kho đến)
  - [ ] `_build_void_movements`: đảo dấu mọi dòng gốc (kể cả 2 dòng của transfer)
- [ ] `inventory/services.py`: `generate_outbound_note_number` (`PX-YYYYMMDD-NNN`)
- [ ] `inventory/models.py` `StockMovement`: thêm `outbound_note` FK (null) + index `ix_sm_outbound_note` + CheckConstraint "đúng 1 nguồn" (cùng đợt với stocktake — gồm đủ 3 FK)
- [ ] `makemigrations inventory` + `migrate`

## Serializers

- [ ] `inventory/serializers.py`: `OutboundNoteLineSerializer` (material_id write / material read, quantity, line_no, note)
- [ ] `inventory/serializers.py`: `OutboundNoteSerializer` (nested lines, `note_type_label`, `status_label`, `total_quantity` = số dòng, validate: site/to_warehouse theo `note_type`, replace-all update)
- [ ] `inventory/serializers.py`: `OutboundNoteListSerializer` (list gọn — không lines)
- [ ] `inventory/serializers.py`: `VoidOutboundNoteSerializer` (reason required)
- [ ] `inventory/serializers.py`: `SimpleSiteSerializer` (`{id, code, name}`) + `SimpleOutboundNoteSerializer` (`{id, number}`) cho `StockMovementSerializer`
- [ ] `StockMovementSerializer`: thêm `outbound_note` / `stocktake_note` (nullable)

## Views / Filters / URLs

- [ ] `inventory/views.py`: `OutboundNoteViewSet` (giống InboundNoteViewSet: update/partial_update/destroy chỉ draft, `@action post` → `note.post(user)`, `@action void` → `note.void(reason, user)`)
- [ ] `inventory/filters.py`: `OutboundNoteFilter` — note_type, status, warehouse, to_warehouse, site, date_from, date_to
- [ ] `inventory/urls.py`: register prefix `outbound-notes`

## Permissions

- [ ] Đọc `IsAuthenticated`; ghi/chốt/hủy `IsAdminOrStorekeeper` (giống InboundNote)

## Tests (`inventory/tests.py`)

- [ ] Tạo phiếu xuất cấp → chốt → 1 dòng `outbound_issue_for_use` (−quantity), tồn giảm đúng
- [ ] Tạo phiếu điều chuyển → chốt → **2 dòng** (kho đi −, kho đến +), tồn 2 kho đúng
- [ ] Chốt khi thiếu tồn → 400, không ghi dòng sổ nào
- [ ] Hủy phiếu xuất → tồn về 0, reversal đúng
- [ ] Hủy phiếu điều chuyển → đảo cả 2 dòng
- [ ] `transfer` thiếu `toWarehouseId` → 400; `toWarehouseId == warehouseId` → 400; `issue_for_use` thiếu `siteId` → 400; `transfer` có `siteId` → 400
- [ ] PUT/DELETE phiếu đã chốt → 400; `/void/` thiếu reason → 400
- [ ] Permission: kế toán tạo phiếu → 403, xem → 200
- [ ] Filter note_type / status / warehouse / to_warehouse / site / date

## Seed

- [ ] `inventory/management/commands/seed_outbound_notes.py`: 1 phiếu xuất cấp (kèm site) + 1 phiếu điều chuyển (tự chốt) — xác nhận tồn 2 kho đúng (chạy sau `seed_sites`)
- [ ] `sites/management/commands/seed_sites.py`: 2-3 công trường mẫu

## Tài liệu

- [ ] Check off các mục trên sau khi code (mỗi mục xong → `[x]`)
- [ ] Cập nhật `docs/entities/README.md` — trạng thái Outbound Note
