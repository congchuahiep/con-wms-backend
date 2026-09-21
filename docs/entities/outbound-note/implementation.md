# Implementation Checklist — Outbound Note

> Phase 2 của Stock (sổ kho). Đi cùng: thêm `outbound_note` FK + CheckConstraint "đúng 1 nguồn" vào `StockMovement` (xem [`../stock/implementation.md`](../stock/implementation.md)).

## Model

- [x] `inventory/models.py`: `OutboundNote(BaseNote)`:
  - [x] `class Type(TextChoices)`: `ISSUE_FOR_USE` / `TRANSFER`
  - [x] `note_type` CharField(20) choices, default=`issue_for_use`
  - [x] `to_warehouse` FK → Warehouse (PROTECT, null/blank) — kho đích khi transfer
  - [x] `site` FK → Site (PROTECT, null/blank) — công trường nhận hàng khi issue_for_use
  - [x] `Meta(BaseNote.Meta)`: `db_table="outbound_note"`, verbose "Phiếu xuất", index `to_warehouse` + `site`
- [x] `inventory/models.py`: `OutboundNoteLine`:
  - [x] `outbound_note` FK CASCADE `related_name="lines"`, `material` FK PROTECT, `quantity` Decimal(14,3), `line_no`, `note`, timestamps
  - [x] **Không có** `unit_price` (D5)
- [x] Hooks:
  - [x] `_build_post_movements`: check tồn đủ → `issue_for_use`: 1 dòng `outbound_issue_for_use` (−); `transfer`: 2 dòng `outbound_transfer_to_warehouse` (−, kho đi) + `inbound_transfer_from_warehouse` (+, kho đến)
  - [x] `_build_void_movements`: đảo dấu mọi dòng gốc (kể cả 2 dòng của transfer)
- [x] `inventory/services.py`: `generate_outbound_note_number` (`PX-YYYYMMDD-NNN`)
- [x] `inventory/models.py` `StockMovement`: thêm `outbound_note` FK (null) + index `ix_sm_outbound_note` + CheckConstraint "đúng 1 nguồn" (cùng đợt với stocktake — gồm đủ 3 FK)
- [x] `makemigrations inventory` + `migrate`

## Serializers

- [x] `inventory/serializers.py`: `OutboundNoteLineSerializer` (material_id write / material read, quantity, line_no, note)
- [x] `inventory/serializers.py`: `OutboundNoteSerializer` (nested lines, `note_type_label`, `status_label`, `total_quantity` = số dòng, validate: site/to_warehouse theo `note_type`, replace-all update)
- [x] `inventory/serializers.py`: `OutboundNoteListSerializer` (list gọn — không lines)
- [x] `inventory/serializers.py`: `VoidOutboundNoteSerializer` (reason required)
- [x] `inventory/serializers.py`: `SimpleSiteSerializer` (`{id, code, name}`) + `SimpleOutboundNoteSerializer` (`{id, number}`) cho `StockMovementSerializer`
- [x] `StockMovementSerializer`: thêm `outbound_note` / `stocktake_note` (nullable)

## Views / Filters / URLs

- [x] `inventory/views.py`: `OutboundNoteViewSet` (giống InboundNoteViewSet: update/partial_update/destroy chỉ draft, `@action post` → `note.post(user)`, `@action void` → `note.void(reason, user)`)
- [x] `inventory/filters.py`: `OutboundNoteFilter` — note_type, status, warehouse, to_warehouse, site, date_from, date_to
- [x] `inventory/urls.py`: register prefix `outbound-notes`

## Permissions

- [x] Đọc `IsAuthenticated`; ghi/chốt/hủy `IsAdminOrStorekeeper` (giống InboundNote)

## Tests (`inventory/tests.py`)

- [x] Tạo phiếu xuất cấp → chốt → 1 dòng `outbound_issue_for_use` (−quantity), tồn giảm đúng
- [x] Tạo phiếu điều chuyển → chốt → **2 dòng** (kho đi −, kho đến +), tồn 2 kho đúng
- [x] Chốt khi thiếu tồn → 400, không ghi dòng sổ nào
- [x] Hủy phiếu xuất → tồn về 0, reversal đúng
- [x] Hủy phiếu điều chuyển → đảo cả 2 dòng
- [x] `transfer` thiếu `toWarehouseId` → 400; `toWarehouseId == warehouseId` → 400; `issue_for_use` thiếu `siteId` → 400; `transfer` có `siteId` → 400
- [x] PUT/DELETE phiếu đã chốt → 400; `/void/` thiếu reason → 400
- [x] Permission: kế toán tạo phiếu → 403, xem → 200
- [x] Filter note_type / status / warehouse / to_warehouse / site / date

## Seed

- [x] `inventory/management/commands/seed_outbound_notes.py`: 1 phiếu xuất cấp (kèm site) + 1 phiếu điều chuyển (tự chốt) — xác nhận tồn 2 kho đúng (chạy sau `seed_sites`)
- [x] `sites/management/commands/seed_sites.py`: 2-3 công trường mẫu

## Tài liệu

- [x] Check off các mục trên sau khi code (mỗi mục xong → `[x]`)
- [x] Cập nhật `docs/entities/README.md` — trạng thái Outbound Note
