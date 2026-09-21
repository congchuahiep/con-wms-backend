# Context cho agent thực thi — OutboundNote + StocktakeNote + Site

> Agent mới cần đọc context này trước rồi tự bắt tay vào các checklist ở `docs/entities/{site,outbound-note,stocktake}/implementation.md`. Đã có đầy đủ design docs, validate Context7, change-logs — không cần hỏi user nữa. Chỉ code, check off checklist, báo cáo.

## TL;DR

Triển khai 3 entity mới (Site, OutboundNote, StocktakeNote) + thêm 2 FK mới vào `StockMovement` + 2 `CheckConstraint` + 2 index. Tất cả nằm trong app `inventory` (trừ `Site` ở app `sites`). Mọi thứ tuân theo kiến trúc `BaseNote` đã có ở `inventory/models.py`.

## Bối cảnh quan trọng — đọc trước

- **`BaseNote` đã tồn tại.** File `con-wms/inventory/models.py` đã có abstract model `BaseNote` (gồm field khung + index `(date/status/warehouse)` + properties `is_draft/is_posted/is_voided` + methods `post(user)` + `void(reason, user)` + 2 hook `_build_post_movements`/`_build_void_movements`). `InboundNote` đã kế thừa xong (`InboundNote(BaseNote)` với `_build_post_movements`/`_build_void_movements` riêng).
    - **2 điểm kỹ thuật bắt buộc** khi tạo model mới kế thừa `BaseNote`:
        1. `Meta(BaseNote.Meta)` (không phải `class Meta:`) để kế thừa index
        2. `indexes = [*(index.clone() for index in BaseNote.Meta.indexes), <index riêng>]` — vì Django **THAY THẾ** (không gộp) index khi child tự khai báo. Đã có ở `InboundNote` — copy pattern.
- **`StockMovement` lưu dòng sổ kho**. `inbound_note` FK đang NOT NULL. Sẽ thêm `outbound_note` + `stocktake_note` FK (cả 2 nullable) + 2 CheckConstraint + 2 index.
- **`MovementType` đã có sẵn 6 giá trị** trong `StockMovement.Type` (nested enum — `inbound_purchase_from_supplier`, `inbound_return_from_site`, `outbound_issue_for_use`, `outbound_transfer_to_warehouse`, `inbound_transfer_from_warehouse`, `stocktake_adjustment`) — phase 1 chỉ dùng 2 giá trị inbound. Code 3 entity mới dùng đúng các giá trị đã có, KHÔNG tạo enum mới.
- **Validate Context7 đã xong** — ghi kết quả vào change-log của từng entity khi triển khai:
    - Django 6.0: `CheckConstraint` + `Q(...)` cho "đúng 1 nguồn" (3 FK nullable); `AlterField` đổi FK → nullable OK (SQLite/Postgres); `Sum` aggregate
    - DRF: writable nested serializer (`transaction.atomic`), `@action(detail=True, methods=["post"])`, `SerializerMethodField`

## 4 entity doc đọc song song (đã đầy đủ, không cần tra thêm)

1. `con-wms/docs/entities/site/README.md` + `model.md` + `api.md` + `auth.md` + `implementation.md` + `change-log.md`
2. `con-wms/docs/entities/outbound-note/` (6 file tương tự)
3. `con-wms/docs/entities/stocktake/` (6 file tương tự)
4. `con-wms/docs/entities/stock/model.md` §2.1, §2.2, §6, §5 — phần StockMovement đã update cho phase 2/3 (3 FK + 2 CheckConstraint) + `change-log.md` v1.5

## File map — thay đổi nằm ở đâu

```
con-wms/
├── config/
│   └── settings.py                    # thêm app "sites" vào INSTALLED_APPS
├── sites/                             # app MỚI cho Site
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py                      # Site model
│   ├── serializers.py                 # SiteSerializer
│   ├── views.py                       # SiteViewSet
│   ├── filters.py                     # (không cần — Site là master data, không filter)
│   ├── admin.py
│   ├── urls.py                        # /api/sites/
│   ├── migrations/
│   │   └── 0001_initial.py            # makemigrations tự sinh
│   ├── tests.py
│   └── management/commands/
│       └── seed_sites.py              # 2-3 công trường mẫu
├── inventory/
│   ├── models.py                      # + OutboundNote, OutboundNoteLine, StocktakeNote, StocktakeLine
│   │                                  #   + 3 FK mới + 2 CheckConstraint + 2 index trên StockMovement
│   │                                  #   + InboundNote: thêm `site` FK + index `ix_inbound_note_site`
│   │                                  #   (KHÔNG đụng BaseNote / InboundNote vòng đời)
│   ├── services.py                    # + generate_outbound_note_number (PX-...)
│   │                                  # + generate_stocktake_note_number (PK-...)
│   ├── serializers.py                 # + OutboundNoteSerializer, StocktakeNoteSerializer, nested lines
│   │                                  #   + SimpleSiteSerializer, SimpleOutboundNoteSerializer, SimpleStocktakeNoteSerializer
│   │                                  #   + VoidOutboundNoteSerializer, VoidStocktakeNoteSerializer
│   │                                  #   + StockMovementSerializer: thêm outboundNote/stocktakeNote
│   │                                  #   + InboundNoteSerializer: thêm siteId/site (validation, replace-all update)
│   ├── filters.py                     # + OutboundNoteFilter, StocktakeNoteFilter
│   │                                  #   + InboundNoteFilter: thêm `site`
│   ├── views.py                       # + OutboundNoteViewSet, StocktakeNoteViewSet (mirror InboundNote)
│   │                                  #   + InboundNoteViewSet.select_related("site")
│   ├── urls.py                        # register outbound-notes, stocktake-notes
│   ├── tests.py                       # thêm test class mới (xem implementation.md của từng entity)
│   └── management/commands/
│       ├── seed_outbound_notes.py     # 1 phiếu xuất cấp + 1 phiếu điều chuyển
│       └── seed_stocktake_notes.py    # 1 phiếu kiểm kê + vài dòng lệch
└── docs/entities/
    ├── README.md                      # đã update — Site ở row 4, renumber
    ├── site/                           # 6 file
    ├── outbound-note/                  # 6 file
    ├── stocktake/                      # 6 file
    ├── inbound-note/                   # đã update (v2.4 — site FK, change-log)
    ├── stock/                          # đã update (v1.5 — 3 FK + 2 CheckConstraint)
    └── material/, supplier/, etc.      # KHÔNG đụng
```

## Thứ tự triển khai đề xuất (mỗi bước chạy test ngay sau đó để bắt lỗi sớm)

> Lý do thứ tự: mỗi bước tự hoàn chỉnh + dựa trên bước trước (nhưng đủ độc lập để lỗi 1 cái không kéo cái sau).

### Bước 1 — `Site` entity (app `sites`)

- Mới hoàn toàn, không phụ thuộc gì → validate pattern trước
- TheMaster data pattern giống `Warehouse`/`Supplier` (xem `con-wms/warehouse/models.py` + `docs/entities/warehouse/model.md`)
- Tests cơ bản: CRUD + permission + soft delete
- **Checkpoint**: `python manage.py test sites` xanh

### Bước 2 — `StockMovement`: thêm 2 FK mới + 2 CheckConstraint + 2 index

- Đây là điểm "neo" — `OutboundNote` và `StocktakeNote` sau này ghi sổ kho vào đây
- Đổi `inbound_note` từ NOT NULL → **nullable** (`AlterField` tự sinh)
- Thêm: `outbound_note` + `stocktake_note` (FK nullable, PROTECT) + `ix_sm_outbound_note` + `ix_sm_stocktake_note`
- Thêm 2 `CheckConstraint` ở `Meta.constraints` (code xem `stock/model.md` §2.1)
- Tests stock hiện có (31 tests) phải **vẫn xanh** sau thay đổi này — quan trọng!
- **Checkpoint**: `python manage.py test inventory` 31/31 xanh

### Bước 3 — `OutboundNote` + `OutboundNoteLine` + hook vào BaseNote

- Kế thừa `BaseNote` (pattern y hệt `InboundNote`, xem `inventory/models.py`)
- Lưu ý `Meta(BaseNote.Meta)` + `indexes = [*(index.clone() for index in BaseNote.Meta.indexes), ...]`
- 2 loại `Type` enum: `ISSUE_FOR_USE` / `TRANSFER` (nested class trong `OutboundNote`)
- FK đặc biệt: `warehouse` (kho xuất, required) + `to_warehouse` (kho đích, PROTECT, chỉ khi transfer) + `site` (công trường, PROTECT, chỉ khi issue_for_use)
- **Hook `_build_post_movements` quan trọng nhất** — check tồn dùng `Sum("quantity").filter(warehouse, material)` aggregate; transfer sinh 2 dòng
- **Hook `_build_void_movements`** — duyệt `self.stock_movements.all()` đảo dấu từng dòng (transfer 2 dòng → 2 reversal)
- Test: gắn `OutboundNoteAPITestCase` vào cuối `inventory/tests.py`
- **Checkpoint**: `python manage.py test inventory` xanh (cộng thêm test mới)

### Bước 4 — `StocktakeNote` + `StocktakeLine` + hook vào BaseNote

- Tương tự Bước 3 — kế thừa `BaseNote`, viết 2 hook
- Dòng phiếu chỉ cần `material` + `difference` (≠ 0) + `reason` (bắt buộc) — **KHÔNG CÓ** `book_quantity`/`counted_quantity` (user bác bỏ v0.1 — xem `stocktake/change-log.md` v0.2)
- Hook `_build_post_movements`: với từng dòng → check `reason` → check `difference ≥ −tồn_hiện_tại` (aggregate `Sum`) → tạo 1 `StockMovement` `movement_type=stocktake_adjustment`, `quantity=difference`, `reason=line.reason`, `stocktake_note=self`
- Test: `StocktakeNoteAPITestCase`
- **Checkpoint**: `python manage.py test inventory` xanh (cộng thêm test mới)

### Bước 5 — `InboundNote` thêm `site` FK

- Liên kết để báo cáo công trường đủ 2 chiều (xuất đi + trả về)
- `site` FK nullable, bắt buộc khi `note_type=return_from_site`, null khi `purchase`
- Cập nhật `InboundNoteSerializer` + `InboundNoteFilter` + `InboundNoteViewSet.select_related`
- Test cập nhật: `test_create_return_with_supplier` thêm `siteId`; thêm test cho `purchase có site → 400`, `return thiếu site → 400`
- **Checkpoint**: full test suite (sites + inventory) xanh

### Bước 6 — Seed commands

- `seed_sites` (chạy đầu tiên, sau đó `seed_inbound_notes` cần Site tồn tại)
- `seed_outbound_notes` (1 xuất cấp + 1 điều chuyển, tự chốt)
- `seed_stocktake_notes` (1 phiếu kiểm kê vài dòng lệch, tự chốt)
- Verify thủ công: chạy `python manage.py seed_<name>`, in tồn kho cuối bằng `seed_stock.py` để xác nhận đúng

## Giành check-off checklist

Với MỖI entity (site/outbound-note/stocktake) + inbound-note v2.4 + stock v1.5: mỗi mục `- [ ]` xong → sửa thành `- [x]` ngay trong `implementation.md` tương ứng. Đến cuối báo cáo: "checklist xong bao nhiêu, còn lại bao nhiêu".

## Quyết định thiết kế **không** được tự ý thay đổi (đã chốt với user)

1. **3 FK concrete trong StockMovement** (không GenericFK, không tách bảng) — xem `stock/model.md` §D10
2. **Transfer 1 phiếu = 1 kho đích** (to_warehouse ở header, không trên dòng) — `outbound-note/model.md` D2
3. **Chặn cứng tồn âm khi chốt xuất** (không cho xuất quá tồn) — `outbound-note/model.md` D4
4. **`destination` = FK Site, KHÔNG free text** — `outbound-note/model.md` D3 + `site/README.md`
5. **`StocktakeLine` chỉ có `difference` + `reason`** (không snapshot book/counted) — `stocktake/model.md` D1, user bác v0.1
6. **App `sites` (số nhiều)** vì `site` trùng module chuẩn Python — `site/model.md` D5
7. **Gộp Stocktake vào app `inventory`** (không tách app) — `stocktake/model.md` D7
8. **`InboundNote.site` bắt buộc khi `return_from_site`** — `inbound-note/model.md` D13
9. **Checklist `unit_price` ⇔ `inbound_purchase_from_supplier`** đã có trong docs nhưng chưa bao giờ có trong code — phase này bổ sung

## Rủi ro cần biết (đã có người phát hiện trước đó)

- **Django bỏ Meta.indexes của base khi child khai báo**: phải `class Meta(BaseNote.Meta)` + clone. Có ở `InboundNote` rồi, copy pattern.
- **Type checker báo `self.lines` / `self.stock_movements` not found**: dùng `# ty: ignore[unresolved-attribute]` (đã có ở `InboundNote._build_post_movements`).
- **Tests cũ có thể fail do field/refactor mới** (`inbound_note` → nullable, v.v.): sửa test tương ứng; chi tiết trong `inbound-note/change-log.md` v2.4.

## Cách validate

```bash
# Sau MỖI bước:
python manage.py makemigrations --check --dry-run  # không drift
python manage.py check                              # không lỗi
python manage.py test sites                         # (sau bước 1)
python manage.py test inventory                     # (sau bước 2-5)

# Cuối cùng:
python manage.py test                               # toàn bộ
```

## Báo cáo cuối cùng cần

- Số tests từng app (sites + inventory) — pass/fail
- Số migration sinh ra
- Checklist `[ ]` → `[x]` cho từng entity
- Bất kỳ chỗ nào **không theo** thiết kế đã chốt → **dừng lại hỏi**, không tự ý đổi
