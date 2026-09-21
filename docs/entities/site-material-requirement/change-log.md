# Change Log — Site Material Requirement (Định mức vật tư công trường)

## v0.1 — 2026-09-20 (design, chờ duyệt)

### Bối cảnh & yêu cầu (user)

Công trường có 1 kho riêng nhưng chưa khai báo được "cần vật tư gì, bao nhiêu". Bổ sung **định mức vật tư** làm mốc so sánh với tồn kho công trường (không giới hạn nhập thêm); khi đủ định mức và hoàn thành → **Tất toán** chuyển vật tư thừa/ngoài định mức về kho khác còn hoạt động.

### Quyết định chốt với user (09/2026-09-20)

| # | Câu hỏi | Quyết định |
|---|---------|------------|
| 1 | Cách so sánh "đủ/thiếu"? | Không có khái niệm "công trường đã sử dụng" — không thao tác nào trừ tồn kho CT theo mức dùng. Định mức là mốc so sánh với **tồn sổ kho** hiện tại. |
| 2 | Phạm vi tất toán? | Hiện bảng + cho chỉnh từng dòng, **mặc định** = phần thừa (vật tư trong định mức) + toàn bộ (vật tư ngoài định mức). **Bổ sung (duyệt 2026-09-20): khi trả ít hơn mặc định phải ghi lý do — lưu vào `note` dòng phiếu tất toán.** |
| 3 | Trạng thái sau tất toán? | **Enum** thay `is_active`; chặn phiếu mới vào kho công trường đã đóng. |
| 4 | Điều kiện mở tất toán? | **Chỉ khi đủ mọi định mức** (chặn cứng). |
| 5 | UI? | Trang chi tiết công trường `/sites/[id]` — thông tin chung + bảng so sánh + sửa công trường + sửa định mức + tất toán. |
| 6 | Đơn vị định mức? | Theo `Material.unit` (không lưu unit riêng). |

### Thiết kế (tóm tắt)

- **Model**: `SiteMaterialRequirement` (site, material, quantity > 0, note; unique `(site, material)`); `Site.status` enum `active/completed/inactive` thay `is_active` (+ `settled_at/by`); đóng kho bằng `Warehouse.is_active=False`.
- **API**: `GET/PUT /api/sites/{id}/requirements/` (bảng so sánh / bulk replace), `POST /api/sites/{id}/settle/` (tất toán = 1 `OutboundNote transfer` chốt ngay + đóng site/kho, atomic).
- **Guard**: `BaseNote.post()/void()` + 3 serializer note chặn phiếu vào kho đóng (gồm `to_warehouse` khi điều chuyển).
- **Frontend**: trang `/sites/[id]` + 2 dialog (sửa định mức, tất toán) + cập nhật list theo `status`.

### Validate (Django 6.0 — tài liệu chính thức)

> Context7 MCP **không có sẵn** trong toolset agent — thay bằng tài liệu chính thức `docs.djangoproject.com/en/6.0` (fetch 2026-09-20) + đối chiếu pattern có sẵn trong repo.

| Vấn đề cần validate | Kết luận | Nguồn |
| -------------------- | -------- | ----- |
| Data migration `is_active → status` (RunPython + historical model) | Hợp lệ: dùng `apps.get_model("sites","Site")`, không import model thật; thêm dependency vào migration mới nhất của `catalog`/`iam` nếu truy cập chéo | Django docs /topics/migrations (Data Migrations, Accessing models from other apps) |
| `TextChoices` serialize được trong migration khi thay field | Hợp lệ (Serializing values — enum instances được hỗ trợ) | Django docs /topics/migrations |
| `CheckConstraint`/`UniqueConstraint` conditional | Pattern đã dùng sẵn trong repo (`StockMovement`, `UnitConversion`) — nhất quán | repo `inventory/models.py`, `catalog/models.py` |
| Guard chốt phiếu trong `BaseNote.post()` + serializer `validate()` | Đúng chuẩn DRF/Django: validation ở serializer (tạo/sửa) + backstop ở `post()` (transaction, raise `ValidationError`) — giống `OutboundNote._build_post_movements` kiểm tra tồn | repo `inventory/models.py`, `inventory/serializers.py` |
| `ViewSet` action (`@action`) cho `requirements`/`settle` | Pattern đã dùng cho `post`/`void` của Note viewsets | repo `inventory/views.py` |

### Còn mở (chờ user duyệt)

- Tên entity/endpoint: `site-material-requirement`, endpoint `requirements` + `settle`.
- Settle cho phép chỉnh số lượng tùy ý trong `[0, tồn]` (có thể trả ít hơn mặc định → phần còn lại ở lại trong kho đóng — chấp nhận, chỉ là số liệu lịch sử).
- Soft-delete cũ `DELETE` giờ đặt `status=inactive`; site `completed` giữ qua tất toán.

## v0.1 → v1.0 — 2026-09-20 (user duyệt + triển khai xong)

### Duyệt của user

| # | Ý kiến | Xử lý |
|---|--------|-------|
| 1 | Oke | — |
| 2 | Oke — **cho phép ghi lý do khi trả ít hơn mặc định** | Bổ sung `lines[].note` trong `POST settle`, **bắt buộc** khi `quantity < default_return_quantity`; lưu vào `OutboundNoteLine.note` — đã cập nhật model.md D6, api.md §4, implementation.md |
| 3 | Oke | — |

### Triển khai (tóm tắt)

- Backend: model + 3 migrations (schema/data/remove is_active), services (so sánh + tất toán), API actions `requirements` + `settle`, guard chặn phiếu vào kho đóng (`BaseNote.post/void` + 3 serializer), 23 test `sites` mới (72/72 sites+inventory+warehouse OK), seed định mức mẫu.
- Frontend: trang `/sites/[id]` (info + bảng so sánh + thao tác), 2 dialog (sửa định mức, tất toán), danh sách site theo `status`; `bun run build` + biome sạch.
- Xem chi tiết ở `implementation.md` (mọi checkbox đã tick).