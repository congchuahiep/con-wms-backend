# Implementation Checklist — Site Warehouse (Kho Công Trường)

> ✅ **Đã triển khai xong** (2026-09-19) — sau khi user duyệt thiết kế v1.0.

## A. Backend — Warehouse

- [x] `warehouse/models.py`: thêm `site = models.OneToOneField("sites.Site", null=True, blank=True, on_delete=models.PROTECT, related_name="warehouse")`
- [x] Helper `warehouse_code_for_site(site)` → `("KHO_" + site.code)[:20]` (đặt ở `warehouse/services.py`)
- [x] `warehouse/serializers.py`: thêm `site` đọc-only (id, code, name) vào `WarehouseSerializer`
- [x] `python manage.py makemigrations warehouse` + `migrate`

## B. Backend — Sites (auto-create)

- [x] `sites/apps.py`: thêm `ready()` → đăng ký `post_save` receiver cho `Site`
- [x] `sites/signals.py` (mới): `create_site_warehouse` — chỉ chạy khi `created=True`, gọi service `ensure_site_warehouse`
- [x] `sites/services.py` (mới): `ensure_site_warehouse` — `update_or_create(code=KHO_<code>, defaults={name, site})` idempotent
- [x] Lazy import warehouse trong handler (import trong thân hàm) — tránh lỗi app-loading khi startup
- [x] `sites/serializers.py`: thêm `warehouse` đọc-only vào `SiteSerializer`

## C. Backend — Validation (D6, nhẹ)

- [x] `inventory/serializers.py` (`OutboundNoteSerializer.validate`): kho công trường + `issue_for_use` → bắt buộc `site == warehouse.site`
- [x] (Kiểm tra) `InboundNoteSerializer.validate`: `purchase` vẫn chặn `site` FK — không đổi behavior

## D. Tests

- [x] `sites/tests.py`: 6 tests — auto-create kho, update không tạo kho thứ 2, code dài cắt 20, soft-delete giữ kho, kho thường `site=null`, 1-1
- [x] `warehouse/tests.py`: serializer list trả `site` (kho CT + kho thường `null`); xóa kho công trường bị chặn (400)
- [x] `inventory/tests.py`: `OutboundSiteWarehouseTestCase` — sai site 400, đúng site 201, kho trung tâm + site bất kỳ vẫn 201
- [x] Chạy `python manage.py test sites warehouse inventory` → **54/54 OK**

## E. Seed data

- [x] `sites/.../seed_sites.py`: gọi `ensure_site_warehouse` cho mỗi site (+ summary số kho công trường)
- [x] `inventory/.../seed_notes.py`: bias mua giao thẳng (70% nhập mua vào kho CT), xuất dùng tại CT tuân thủ D6
- [x] `warehouse/.../seed_warehouses.py` + `sites/.../seed_sites.py`: seed 2 kho trung tâm + 5 công trường (5 kho CT), dọn kho/site mẫu cũ
- [x] Chạy lại `python manage.py seed_all --reset` → **50 phiếu** (40 nhập: 28 kho CT + 12 kho trung tâm; 6 xuất; 4 điều chỉnh), 259 dòng sổ kho, 0 tồn âm

## F. Frontend (con-wms-frontend)

- [x] `features/site/types.ts`: thêm `warehouse: SimpleWarehouseRef | null`
- [x] `features/warehouse/types.ts`: thêm `site: SimpleSiteRef | null`
- [x] `features/warehouse/components.tsx` (`WarehouseSelectField`): sort kho trung tâm trước, nhãn kèm `(CT_RG)` — dùng chung inbound/outbound
- [x] Trang Công trường (`sites/columns.tsx`): cột "Kho công trường" hiện mã `KHO_CT_RG`
- [x] Trang Quản lý kho (`warehouses/page.tsx` + `item.tsx`): hiển thị **cả kho công trường** (dùng `includeSite: true`), phân biệt bằng badge "Kho công trường · CT_RG"
- [x] Form phiếu xuất (`notes/outbound/note-form.tsx`): nhãn kho đích kèm mã công trường
- [~] Form phiếu nhập: chọn kho công trường từ dropdown đã gắn nhãn (chưa tự động gán khi chọn công trường — đơn giản hóa, D6 chặn ở backend)
- [x] `bun run build` (TypeScript sạch) + `bunx biome check`

## G. Tài liệu

- [x] Cập nhật `docs/entities/README.md` (index thêm row) + `site/change-log.md` + `warehouse/change-log.md`

## Ghi chú bổ sung trong lúc triển khai

- Khám phá: các test cũ của `warehouse` (POST/PUT không `format="json"`) fail sẵn từ trước do config camelCase + DRF test client — đã chuẩn hoá theo convention `inventory` (`format="json"`).
- `material/components.tsx` + `material/types.ts` (SimpleMaterial.unit) là WIP của user chưa đồng bộ — đã vá `toSimpleMaterial` tối thiểu để build xanh (unit=object→chuỗi code).