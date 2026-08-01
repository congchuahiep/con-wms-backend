# Project Charter & Scope — con-wms

> Tài liệu mức dự án (Project Charter) cho hệ thống quản lý vật tư `con-wms`.
> Phục vụ cả hai mục tiêu: xây dựng phần mềm thực cho công ty xây dựng địa phương (quy mô nhỏ) và hoàn thành bài tập lớn.
> Phiên bản: v0.1 — khởi tạo ban đầu.

---

## 1. Tên dự án

`con-wms` — Hệ thống quản lý vật tư (Warehouse Management System) cho công ty xây dựng địa phương (quy mô nhỏ).

## 2. Bối cảnh & lý do

Công ty xây dựng địa phương (xã), quy mô **~10 người**, hiện quản lý vật tư bằng sổ sách/Excel. Khi khối lượng công việc tăng, ghi chép tay dẫn tới: sai số, khó truy vết, kiểm kê mất thời gian, không nắm được tồn kho theo thời gian thực.

Hệ thống cần giúp: lưu trữ danh mục vật tư, quản lý nhiều kho có định vị, ghi nhanh nhập/xuất bằng đầu đọc barcode kiểu siêu thị (USB HID), lưu nhà cung cấp kèm lịch sử giao dịch, kiểm kê nhanh để điều chỉnh tồn thực tế.

## 3. Mục tiêu dự án (SMART)

- **Nghiệp vụ:** Giảm thời gian ghi nhận nhập/xuất từ "vài phút/phiếu" xuống **< 30 giây/phiếu** nhờ barcode; độ chính xác sổ sách ≥ 99% sau kiểm kê.
- **Sản phẩm:** Web app dùng được 100% trên máy văn phòng công ty, không cần cài đặt app, không cần kết nối internet ngoài (chỉ cần mạng LAN).
- **Học thuật:** Hoàn chỉnh 1 dự án full-stack có đủ 5 chức năng cốt lõi, có tài liệu thiết kế rõ ràng.

## 4. Đối tượng sử dụng (Stakeholders)

| Vai trò               | SL  | Nhiệm vụ chính                          |
| --------------------- | --- | --------------------------------------- |
| Quản lý (chủ công ty) | 1   | Xem báo cáo/dashboard, ra quyết định    |
| Thủ kho               | 1–2 | Nhập/xuất/kiểm kê, điều chỉnh tồn       |
| Chủ nhiệm công trình  | 2–3 | Đề xuất xuất vật tư, theo dõi xuất dùng |
| Kế toán               | 1   | Xem lịch sử giao dịch với NCC           |
| Admin hệ thống        | 1   | Quản trị user, danh mục                 |

## 5. Phạm vi sản phẩm (Product Scope)

### 5.1. Trong phạm vi (In-scope) — 5 chức năng cốt lõi

#### F1. Quản lý vật tư + Nhập/Xuất + Barcode

- Danh mục vật tư: mã SKU (chuẩn theo mã NCC có sẵn), tên, đơn vị tính, quy cách, nhóm vật tư.
- Phân loại theo nhóm (2 cấp: _Nhóm → Vật tư_).
- Đầu đọc barcode USB HID (hoạt động như bàn phím): quét mã SKU có sẵn để thêm dòng phiếu nhanh.
- Phân biệt loại phiếu:
    - **Nhập:** Nhập mua (từ NCC), Nhập hoàn trả (từ công trường).
    - **Xuất:** Xuất sử dụng (cho công trường/dự án), Xuất điều chuyển (chuyển nội bộ kho).
- Mỗi phiếu có: số phiếu, ngày, loại, kho, NCC (nếu là nhập mua), người lập, danh sách dòng vật tư.

#### F2. Quản lý nhà cung cấp (NCC)

- Thông tin liên hệ: mã NCC, tên, SĐT, email, địa chỉ, người liên hệ, ghi chú.
- Lịch sử giao dịch: xem các phiếu nhập mua liên quan tới NCC (tự tổng hợp từ F1, không tạo riêng).

#### F3. Quản lý nhà kho

- Nhiều kho. Mỗi kho có **cấu trúc vị trí**: _Kho → Khu vực → Kệ → Tầng → Ô_ (đủ để định vị vật tư).
- Vật tư khi nhập được gán vào vị trí. Có thể di chuyển vị trí trong cùng kho.
- Xem/Sơ đồ vị trí (đơn giản) và tìm vị trí đang lưu vật tư.

#### F4. Kiểm kê

- Tạo **phiếu kiểm kê** cho 1 kho (chọn toàn bộ hoặc theo nhóm/khu vực).
- Thủ kho quét/đếm số thực tế từng vị trí.
- Hệ thống tự tính chênh lệch (delta = thực tế − sổ sách).
- **Thủ kho tự điều chỉnh tồn** (không cần xét duyệt) — phù hợp quy mô nhỏ.
- Chênh lệch ghi nhận kèm lý do (hư / mất / sai số / thừa).

#### F5. Báo cáo & Dashboard ("một số thứ nữa")

- Tồn kho hiện tại theo kho/vị trí/nhóm + giá trị tồn (giá nhập gần nhất).
- Nhập – Xuất – Tồn theo kỳ.
- Lịch sử giao dịch với NCC.
- Top vật tư xuất nhiều / tồn lâu.
- Dashboard 1 trang cho quản lý: tồn tổng, số phiếu hôm nay, cảnh báo tồn thấp.

### 5.2. Ngoài phạm vi (Out-of-scope) — KHÔNG làm trong bản đầu

- Quản lý **mua hàng / Purchase Order / báo giá NCC** (scope tách biệt).
- Quản lý **công cụ/dụng cụ phát mượn** (khác vật tư tiêu hao).
- Quản lý **lô / hạn sử dụng / quy cách đóng gói phức tạp**.
- Tính giá xuất theo FIFO/LIFO/FEFO kế toán chính xác — bản đầu dùng **giá nhập gần nhất**.
- App mobile native — chỉ web responsive.
- Offline-first sync — chỉ dùng online trong mạng LAN công ty.
- Đa ngôn ngữ — chỉ tiếng Việt.
- Email/SMS thông báo — chưa cần ở quy mô 10 người.

### 5.3. Có thể mở rộng sau (Future scope)

- Quản lý công cụ/devices phát mượn.
- Lô & FEFO cho vật tư có hạn sử dụng.
- Purchase order + quy trình duyệt phiếu.
- Mobile app (PDA Android) dùng tại công trường.
- Multitenancy / phân quyền chi tiết theo dự án.

## 6. Yêu cầu phi chức năng (Non-functional)

| Nhóm             | Yêu cầu                                                                                                                                                 |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Hiệu năng        | Phiếu ≤ 50 dòng load < 1.5s; quét barcode phản hồi tức thì (< 100ms sau khi mã vạch gửi xong)                                                           |
| Bảo mật          | Đăng nhập JWT, role: admin/thủ kho/chủ nhiệm/kế toán; log thao tác quan trọng (xóa phiếu, điều chỉnh tồn)                                               |
| Khả dụng         | Chạy trên mạng nội bộ LAN công ty; uptime mục tiêu trong giờ hành chính ~ 99%                                                                           |
| Năng lực sử dụng | Thủ kho có thể ≥ 45 tuổi, ít tin học — UI phải lớn, ít nút, phím tắt Enter để xuống dòng tiếp theo khi nhập phiếu                                       |
| Khả bảo trì      | Tách module Django apps theo nghiệp vụ: catalog, inventory, warehouse, supplier, stocktake, reports, users                                              |
| Nền tảng         | Backend: Django 6 + DRF + SQLite/PostgreSQL; Frontend: Next.js (App Router) + TailwindCSS, lấy dữ liệu qua REST; barcode USB HID (gõ thẳng vào ô input) |
| Triển khai       | Chạy trên 1 máy chủ văn phòng (Windows hoặc Linux), Docker compose tùy chọn                                                                             |

## 7. Rủi ro & giải pháp

| Rủi ro                                     | Tác động        | Giảm thiểu                                                              |
| ------------------------------------------ | --------------- | ----------------------------------------------------------------------- |
| Mã SKU NCC có thể trùng hoặc sai định dạng | Phiếu sai       | Có chức năng map SKU → vật tư nội bộ, thủ kho xác nhận trước khi lưu    |
| Thủ kho ít dùng máy                        | Chậm nghiệm thu | UI tối giản, phím tắt, dữ liệu nhập chủ yếu qua quét                    |
| SQLite không đủ tải                        | Chậm báo cáo    | Thiết kế schema đúng; sẵn sàng chuyển PostgreSQL (cùng chuỗi migration) |
| Scope creep                                | Trễ tiến độ     | Bám scope §5.2, mọi yêu cầu mới đưa vào "Future scope"                  |

## 8. Trọng số ưu tiên (MoSCoW)

- **Must:** F1, F3 (đa kho + định vị), F5 (tồn kho hiện tại + dashboard).
- **Should:** F2 lịch sử giao dịch, F4 kiểm kê.
- **Could:** Báo cáo nhập-xuất-tồn kỳ, di chuyển vị trí nội bộ.
- **Won't (bản đầu):** PO, lô/FEFO, app mobile, duyệt phiếu.

## 9. Cột mốc (Milestones)

1. **M1:** Domain model + API contract (OpenAPI qua drf-spectacular) + seed data.
2. **M2:** F1 + F5 dashboard tối thiểu (vòng lặp quét – nhập – xuất – xem tồn chạy được).
3. **M3:** F2 + F3 đa kho định vị.
4. **M4:** F4 kiểm kê.
5. **M5:** Báo cáo kỳ + UI hoàn thiện + nghiệm thu.

## 10. Giả định & ràng buộc

- Công ty có **đầu đọc barcode USB HID** (giả lập bàn phím) — không cần PDA Android.
- Phiên làm việc đồng thời tối đa ~5 người; không yêu cầu high-concurrency.
- Đây đồng thời là bài tập lớn — phải đảm bảo rõ ràng về mặt tài liệu thiết kế.

## 11. Người phê duyệt

| Vai trò               | Họ tên | Chữ ký |
| --------------------- | ------ | ------ |
| Chủ công ty (sponsor) |        |        |
| Giảng viên hướng dẫn  |        |        |
| Dev (bạn)             |        |        |
