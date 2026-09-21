# Change Log — Site Warehouse (Kho Công Trường)

## v1.0 — 2026-09-19 (Thiết kế — chờ duyệt)

### Bối cảnh

User đặt câu hỏi: model hiện tại buộc "mua → nhập kho chính → xuất ra công trường", trong khi thực tế **NCC giao thẳng tới công trường** rất phổ biến (có khi nhiều hơn mua về kho). Đồng thời: "một công trường cũng có chứa một nhà kho" — trong thực tế công trường có kho/bãi vật tư (thủ kho công trường = `Site.manager`).

### Phân tích 3 phương án (trình user)

| Phương án | Mô tả                                                             | Trade-off                                                                  |
| --------- | ----------------------------------------------------------------- | -------------------------------------------------------------------------- |
| **A**     | Công trường có kho thật, track tồn + thêm bước "xuất dùng tại CT" | Đầy đủ nhất nhưng thêm 1 bước ghi chép khi thi công                        |
| **B**     | Phiếu "nhập thẳng CT" không qua kho, không sinh sổ kho            | Đơn giản nhưng tạo 2 hệ dữ liệu (phiếu không nằm trong sổ kho) cho kế toán |
| **C**     | Mỗi CT có 1 kho liên kết; tận dụng toàn bộ luồng phiếu hiện có    | Ít đụng code nhất, sổ kho nhất quán                                        |

### Quyết định chốt với user

> **Phương án C (điều chỉnh):** kho công trường **tự động tạo** khi tạo công trường mới, quan hệ **1-1** (`Warehouse.site` OneToOneField). **Không ghi vị trí** (kho = bãi chứa). Công trường **chỉ cần theo dõi số lượng vật tư đã nhập là chính**.

| #   | Quyết định                                                                   | Nguồn                                                                      |
| --- | ---------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| D1  | `Warehouse.site` OneToOneField null=True — thay vì Site sở hữu danh sách kho | User: "đây sẽ là mối quan hệ 1-1 luôn"                                     |
| D2  | Auto-create qua signal `post_save` trên Site                                 | User: "Kho công trường sẽ tự động tạo khi tạo một công trường mới"         |
| D3  | Code kho = `KHO_<SITE_CODE>`                                                 | Quy ước code repo                                                          |
| D4  | Không thêm vị trí/location                                                   | User: "kho tồn tại như 1 bãi chứa đồ, không cần ghi lại vị trí gì cả"      |
| D5  | Không đổi model inventory                                                    | Tận dụng luồng phiếu generic theo `warehouse`                              |
| D6  | Validation: kho công trường chỉ `issue_for_use` cho chính site của nó        | Chống dữ liệu lệch                                                         |
| D7  | Track "đã nhập" là chính; "xuất dùng tại CT" là tùy chọn                     | User: "công trường cũng chỉ cần theo dõi số lượng vật tư đã nhập là chính" |

### Kết quả validate Context7 (2026-09-19)

- `/websites/djangoproject_en_6_0` — One-to-one models: `OneToOneField` + `on_delete`; **object cha phải save trước khi gán vào OneToOne** → tạo kho trong `post_save` (instance đã lưu) là đúng pattern.
- `/websites/djangoproject_en_6_0` — Related objects: dùng `update_or_create`/`get_or_create` cho auto-create idempotent.
- DRF: không cần pattern mới — `SimpleWarehouseSerializer`/nested read-only đã dùng sẵn trong codebase (`InboundNoteSerializer.warehouse`).

### Trạng thái

📝 **Chờ user duyệt — chưa code** (entity-workflow Bước 3). Code theo checklist [`implementation.md`](implementation.md).
