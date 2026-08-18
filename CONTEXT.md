# Con-WMS

Hệ thống quản lý vật tư kho cho công ty xây dựng địa phương (~10 người, 1–3 kho bãi chứa). Glossary này chốt từ ngữ nghiệp vụ dùng chung trong docs và code.

## Chứng từ

**Phiếu (Note)**:
Chứng từ ghi nhận một giao dịch kho: phiếu nhập (InboundNote), phiếu xuất (OutboundNote), phiếu kiểm kê (StocktakeNote).
_Avoid_: đơn hàng, hóa đơn, receipt

**Phiếu nhập (Inbound note)**:
Phiếu ghi nhận hàng vào kho; hai loại: nhập mua (có nhà cung cấp, có đơn giá) và nhập hàng công trường trả lại (không nhà cung cấp, không đơn giá).
_Avoid_: đơn nhập hàng, order, nhập hoàn trả (gây nhầm: đọc như trả hàng cho NCC)

**Nháp (Draft)**:
Trạng thái phiếu đang soạn; chưa ảnh hưởng tồn kho, xóa được.
_Avoid_: tạm, pending

**Chốt phiếu (Post)**:
Hành động chuyển phiếu nháp → đã chốt; hệ thống ghi sổ kho, tồn thay đổi. Sau khi chốt, phiếu không sửa được.
_Avoid_: duyệt, approve (không có ai duyệt phiếu)

**Hủy phiếu (Void)**:
Vô hiệu hóa phiếu đã chốt bằng cách ghi dòng sổ kho ngược dấu; phiếu vẫn còn trong sổ sách để kế toán tra. Bắt buộc ghi lý do.
_Avoid_: xóa, delete

## Tồn kho

**Sổ kho (Stock movement)**:
Dòng ghi sổ bất biến phát sinh khi chốt/hủy phiếu; là nguồn sự thật duy nhất của tồn kho.
_Avoid_: inventory transaction, ledger, bút toán

**Tồn kho (Stock balance)**:
Số lượng hiện có của một vật tư tại một kho, tính bằng tổng các dòng sổ kho — không phải bảng dữ liệu lưu riêng.
_Avoid_: stock level, quantity on hand

**Kiểm kê (Stocktake)**:
Quy trình đếm hàng thực tế và đối chiếu với sổ sách; chênh lệch ghi nhận kèm lý do (hư / mất / sai số / thừa).
_Avoid_: inventory audit, check stock

**Điều chỉnh tồn (Stock adjustment)**:
Dòng sổ kho sửa chênh lệch giữa sổ sách và thực tế, sinh ra khi chốt phiếu kiểm kê.
_Avoid_: sửa tồn, fix stock

**Giá nhập gần nhất (Last purchase price)**:
Đơn giá của lần nhập mua mới nhất của một vật tư; dùng để định giá trị tồn (F5).
_Avoid_: giá vốn, average cost
