# Change Log — Stock (Sổ kho & Tồn kho)

## v1.5 — 2026-08-18 (Design — chưa code)

Thiết kế OutboundNote + StocktakeNote ([`../outbound-note/`](../outbound-note/README.md), [`../stocktake/`](../stocktake/README.md)) — kéo theo sổ kho:

- `StockMovement` bổ sung `outbound_note` + `stocktake_note` FK (nullable) — đủ 3 nguồn; `inbound_note` NOT NULL → NULL (AlterField)
- CheckConstraint `ck_sm_exactly_one_source` — đúng 1 trong 3 FK (code trong §2.1)
- CheckConstraint `ck_sm_price_only_purchase` — `unit_price` ⇔ `inbound_purchase_from_supplier` (bổ sung constraint đã ghi ở v1.1 nhưng chưa từng có trong code)
- Index `ix_sm_outbound_note` + `ix_sm_stocktake_note`
- `StockMovementSerializer` thêm `outboundNote` / `stocktakeNote` (nullable)
- Validate Context7: `CheckConstraint` + `Q(...)` (3 FK nullable), `AlterField` FK nullable — ✅

## v1.4 — 2026-08-18

Enum gom vào trong model + đồng bộ docs (user chỉnh code cho gọn):

- `MovementType` (module-level) → `StockMovement.Type` — nested enum theo đúng pattern Django docs (`Student.YearInSchool`), validate Context7 ✅
- `NoteType` / `NoteStatus` → `InboundNote.Type` / `BaseNote.Status`
- Label `noteType` đổi: "Nhập mua" → "Mua hàng từ nhà cung cấp", "Nhập hàng công trường trả lại" → "Công trường trả lại hàng" (ảnh hưởng `noteTypeLabel` trong API)
- `total_quantity` = **số dòng vật tư** (integer) — user chốt, khác với trước (tổng số lượng); đã cập nhật test + `docs/entities/inbound-note/api.md`
- Không sinh migration mới (giá trị enum giữ nguyên)

## v1.3 — 2026-08-18

Refactor: gom vòng đời chung của mọi phiếu vào abstract base `BaseNote` (user chốt; design doc cho Outbound/Stocktake hoãn vì frontend có ý kiến khác):

- `BaseNote` (abstract, `inventory/models.py`): field khung (number, status, date, warehouse, note, created_by, voided_*, timestamps) + index chung (`ix_%(class)s_date/status/warehouse`) + vòng đời `post(user)` / `void(reason, user)` + properties `is_draft/is_posted/is_voided`
- `InboundNote(BaseNote)`: giữ `note_type` + `supplier`, viết 2 hook `_build_post_movements` / `_build_void_movements` (logic cũ từ `services.py`)
- `services.py`: chỉ còn `generate_inbound_note_number`; `views.py` gọi `note.post()` / `note.void()`
- Lưu ý Django: child tự khai báo `Meta.indexes` sẽ THAY THẾ index của base → child phải `class Meta(BaseNote.Meta)` + nối `*(index.clone() for index in BaseNote.Meta.indexes)`
- Migration 0004 (bỏ index cũ, alter field) + 0005 (thêm index mới `ix_inboundnote_*`)

## v1.2 — 2026-08-14

Đổi tên enum `MovementType` + `NoteType` cho minh bạch (user phản hồi tên cũ gây nhầm lẫn, vd "Nhập hoàn trả" đọc như trả hàng cho NCC):

| Giá trị cũ | Giá trị mới | Label mới |
|---|---|---|
| `inbound_purchase` | `inbound_purchase_from_supplier` | Nhập kho: mua hàng từ nhà cung cấp |
| `inbound_return` | `inbound_return_from_site` | Nhập kho: công trường trả lại hàng |
| `outbound_use` | `outbound_issue_for_use` | Xuất kho: cấp phát để sử dụng |
| `transfer_out` | `outbound_transfer_to_warehouse` | Xuất kho: điều chuyển sang kho khác |
| `transfer_in` | `inbound_transfer_from_warehouse` | Nhập kho: điều chuyển từ kho khác |
| `stocktake_adjust` | `stocktake_adjustment` | Điều chỉnh tồn: chênh lệch kiểm kê |

- `NoteType.return` → `return_from_site` (label: "Nhập hàng công trường trả lại")
- Quy ước đặt tên: giá trị bắt đầu bằng hướng tồn kho (`inbound_` / `outbound_` / `stocktake_`), phần sau nói rõ lý do + đối tượng
- Migration `0002` (AlterField: `movement_type` max_length 20→40) + `0003` (data migration đổi giá trị cũ → mới)
- Cập nhật code tham chiếu: `models.py`, `services.py`, `views.py`, `serializers.py`, `tests.py`, `seed_inbound_notes.py`
- Test: 31/31 pass sau khi đổi tên
- Ghi chú cho frontend: [`frontend-migration.md`](frontend-migration.md)

## v1.1 — 2026-08-13

Làm rõ sau khi user hỏi về 3 FK nguồn nullable:

| # | Thay đổi | Lý do |
|---|---|---|
| 1 | Thêm D10 — chốt lý do dùng 3 concrete FK thay vì GenericForeignKey/tách bảng | Ghi lại trade-off để sau này không ai "sửa" thành GenericFK |
| 2 | Làm rõ: phase 1 chỉ có `inbound_note` NOT NULL — **không có NULL nào** lúc code | Bảng 15 field là hình dạng đích, tránh hiểu nhầm |
| 3 | Thêm CheckConstraint `unit_price` ⇔ `inbound_purchase` | Siết phụ thuộc trường theo loại dòng |

## v1.0 — 2026-08-13

Khởi tạo thiết kế sau khi thảo luận kiến trúc với user:

- **ADR-0001**: sổ kho (`StockMovement`) là nguồn sự thật duy nhất — không có bảng tồn ghi đè
- 1 model `StockMovement` bất biến: không update, không delete, không API write trực tiếp
- Tồn kho = `SUM(quantity)` theo (kho, vật tư) — **không có Location** (nhất quán Warehouse D1)
- `quantity` có dấu (+/−); `unit_price` chỉ cho nhập mua → nuôi "giá nhập gần nhất" (F5)
- `date` nghiệp vụ riêng cho báo cáo kỳ (nhập bù phiếu không làm lệch kỳ)
- Hủy phiếu = dòng reversal ngược dấu (`reversal_of`), kèm `reason` bắt buộc
- Cột `lot` chừa sẵn (nullable) — trace theo lô là future scope
- Phân pha: phase 1 chỉ nguồn `inbound_note`; outbound/stocktake thêm sau

### Kết quả validate Context7

| Library | Kết quả |
|---|---|
| Django 6.0 | ✅ `CheckConstraint` + `Q(...)` cho ràng buộc "đúng 1 nguồn FK" — dùng `Q(field__isnull=...)`; lưu ý Oracle < 23c cần thêm điều kiện null tường minh (không liên quan — project dùng SQLite/PostgreSQL) |
| Django 6.0 | ✅ `DecimalField(14,3)`, `TextChoices`, FK `PROTECT`, self-FK `reversal_of` — đúng pattern |

### Triển khai (2026-08-13)

- ✅ `StockMovement` 14 fields + 3 indexes + admin read-only
- ✅ `services.py`: `post_inbound_note` / `void_inbound_note` — transaction.atomic
- ✅ 2 endpoint read-only: `/api/stock/` (tồn + giá nhập gần nhất) + `/api/stock/movements/` (sổ kho, originals_only)
- ✅ 13 tests stock — pass; tổng 31 tests app `inventory`
- ✅ Seed: tồn kho mẫu đúng (Xi măng 110 bao, Cát vàng 5.5 m³)
- ✅ Tạo `docs/adr/0001-stock-movement-ledger.md`
- ⚠️ Dev: bỏ 2 FK `outbound_note`/`stocktake_note` (target model chưa tồn tại) — thêm ở phase 2/3

### Chốt với user (5/5)

| # | Điểm | Kết quả |
|---|---|---|
| 1 | Phiếu có trạng thái nháp → chốt | ✅ Có |
| 2 | Hủy phiếu bắt buộc lý do | ✅ Có |
| 3 | Cấm sửa phiếu đã chốt | ✅ Cấm — hủy + làm lại |
| 4 | Vị trí trong kho | ✅ **Không có** — kho là bãi chứa (Warehouse D1), tồn theo kho |
| 5 | Trace theo lô | ✅ Để sau — chừa cột `lot` |
