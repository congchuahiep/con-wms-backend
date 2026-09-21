# Implementation Checklist — Site Material Requirement (Định mức vật tư công trường)

> ✅ **Đã triển khai xong** (2026-09-20) — sau khi user duyệt design v0.1 (kèm bổ sung: note lý do khi trả ít hơn mặc định).

## A. Backend — Model & Migration (app `sites`)

- [x] `sites/models.py`: `Site.Status` (TextChoices — active/completed/inactive), thay `is_active` bằng `status` (default active), thêm `settled_at`, `settled_by`
- [x] `sites/models.py`: model `SiteMaterialRequirement` (site FK, material FK, quantity Decimal(14,3), note) + `UniqueConstraint(site, material)` + `CheckConstraint(quantity > 0)`
- [x] `sites/admin.py`: đăng ký `SiteMaterialRequirementAdmin` + inline trên `SiteAdmin`
- [x] Migrations `sites`: `0002` (schema — status/settled_*/table mới) + `0003` (data migration `is_active → status`, RunPython historical models) + `0004` (remove `is_active`) — đã `migrate` OK
- [x] `python manage.py makemigrations --check` → No changes detected

## B. Backend — Service (app `sites`)

- [x] `sites/services.py`:
  - [x] `site_stock_balances(site)` — aggregate `StockMovement` theo `(warehouse=site.warehouse, material)` (SUM quantity)
  - [x] `build_requirement_rows(site)` — hợp định mức + tồn > 0 → rows `{material, required_quantity, balance, status, default_return_quantity}`
  - [x] `settle_site(site, to_warehouse, lines, user)` — atomic: tạo + chốt `OutboundNote(transfer)` (dùng `generate_outbound_note_number`), set `status=completed` + `settled_at/by`, `warehouse.is_active=False`; validate đủ định mức / dòng / **note bắt buộc khi trả < mặc định** → lưu vào `OutboundNoteLine.note`

## C. Backend — API (app `sites`)

- [x] `sites/serializers.py`:
  - [x] `SiteSerializer`: bỏ `is_active`, thêm `status`, `statusLabel`, `settledAt`, `settledBy`
  - [x] `SiteRequirementRowSerializer` (output so sánh — decimal dạng string)
  - [x] `RequirementsUpdateSerializer` (`{lines: [{materialId, quantity>0, note}]}` — validators: trùng vật tư)
  - [x] `SettleSerializer` (`{toWarehouseId, lines: [{materialId, quantity, note}]}` — validators: trùng vật tư)
- [x] `sites/views.py` (`SiteViewSet`):
  - [x] `list`: param `?status=` (active|completed|inactive|all), mặc định active; detail/actions trả mọi site
  - [x] `destroy`: đặt `status=inactive`
  - [x] action `requirements` — `GET` (bảng so sánh) + `PUT` (bulk replace) — permission: GET `IsAuthenticated`, PUT `IsAdmin`
  - [x] action `settle` — `POST` — `IsAdmin`; chuyển django `ValidationError` → DRF 400
- [x] `sites/urls.py`: router nhận action tự động (`sites/{id}/requirements/`, `sites/{id}/settle/`)

## D. Backend — Guard chặn phiếu vào kho đã đóng (app `inventory`)

- [x] `inventory/models.py` `BaseNote.post()`/`void()`: `_assert_warehouse_open()` — chặn khi `warehouse.is_active=False` hoặc `warehouse.site.status != active`
- [x] `inventory/serializers.py`: `_ensure_warehouse_open()` — gọi trong `InboundNoteSerializer.validate` (warehouse), `OutboundNoteSerializer.validate` (warehouse + to_warehouse), `StocktakeNoteSerializer.validate` (warehouse)

## E. Backend — Tests

- [x] `sites/tests.py` (23 tests OK):
  - [x] Định mức: PUT replace/bulk rỗng, quantity ≤ 0 → 400, trùng vật tư → 400, site đã đóng → 400, GET readable bởi user thường
  - [x] GET requirements: gộp định mức + tồn, trạng thái sufficient/insufficient/not_in_plan, `defaultReturnQuantity`
  - [x] Settle: thành công (phiếu PX… posted, sổ kho ±, site completed, kho đóng, tồn 2 đầu đúng); chưa đủ định mức → 400; line > tồn → 400; kho đích đóng → 400; trả ít hơn mặc định thiếu lý do → 400 (đủ lý do → thành công + lưu note); settle lần 2 → 400; chặn phiếu mới sau đóng (serializer + BaseNote.post)
  - [x] List filter default active / `?status=all`; destroy → `status=inactive`
- [x] `inventory/tests.py` + `warehouse/tests.py` không regress (49 tests OK)
- [x] Chạy `python manage.py test sites inventory warehouse` → **72/72 OK** (toàn repo 129 tests — 3 lỗi `catalog` là **pre-existing**, không liên quan: test đối chiếu chuỗi `—`/`-` và error shape cũ trước custom exception handler)

## F. Seed

- [x] `seed_sites.py`: dùng `status` thay `is_active` + gán định mức mẫu (CT_RG: XM-HT-PCB40 100, GACH-ONG 20000; CT_NHA_XUONG: THEP-D10 5000, DA-1X2 120)
- [x] `seed_notes.py`: `Site.objects.filter(status=Site.Status.ACTIVE)`
- [x] `python manage.py seed_all --reset` chạy OK (5 CT + 4 dòng định mức, 50 phiếu, 259 dòng sổ)

## G. Frontend (con-wms-frontend)

- [x] `src/configs/endpoints.ts`: `authEndpoints.sites` thêm `requirements(id)`, `settle(id)`
- [x] `src/configs/querykeys.ts`: `siteKeys.requirements(id)`
- [x] `src/features/site/types.ts`: `Site` bỏ `isActive` → `status/statusLabel/settledAt/settledBy`; `SiteRequirementRow`; `SettleInput`/`SettleResponse`
- [x] `src/features/site/schemas.ts`: `RequirementLineSchema`, `RequirementsUpdateSchema`, `SettleLineSchema`, `SettleSchema` (Valibot)
- [x] `src/features/site/services.ts`: `useGetSiteRequirements`, `useUpdateSiteRequirements` (PUT), `useSettleSite` (POST, invalidate sites + stock)
- [x] `src/features/site/utils.ts`: `SITE_STATUS_OPTIONS/LABELS`, `siteStatusLabel`, `toRequirementsInput`, `requirementStatusLabel`
- [x] **Trang chi tiết** `src/app/(app)/sites/[id]/page.tsx`: header + badge trạng thái; info card; bảng so sánh định mức vs tồn (Định mức / Tồn / `min/định mức` / Trạng thái / Trả về khi tất toán); cảnh báo thiếu định mức; khu Thao tác (sửa CT, sửa định mức, Tất toán)
- [x] `requirements-dialog.tsx`: Formisch + field array (MaterialComboboxField + số lượng + ghi chú, thêm/xóa dòng)
- [x] `settle-dialog.tsx`: chọn kho đích (kho đang hoạt động, loại kho của chính site), dòng trả về mặc định = `defaultReturnQuantity`, nhắc **ghi lý do khi trả ít hơn**, chặn khi thiếu định mức
- [x] Danh sách site: `use-site-params.ts` (`status` filter), `filter-bar.tsx` (select active/completed/inactive/all), `columns.tsx` (badge trạng thái + link chi tiết + ẩn xóa khi không active), `page.tsx`
- [x] `bun run build` xanh + `bunx biome check` 13 file sạch (lint toàn repo có ~595 lỗi **pre-existing**, không do thay đổi này)

## H. Tài liệu

- [x] Cập nhật `docs/entities/README.md` (index + row 12)
- [x] Cập nhật `site/change-log.md` (v1.2 — breaking `is_active` → `status`)
- [x] `change-log.md` của entity này: ghi nhận duyệt + triển khai