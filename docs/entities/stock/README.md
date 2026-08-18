# Stock (Sổ kho & Tồn kho) — Index

Django app: **`inventory`**

Entity này trả lời câu hỏi **"trong kho còn bao nhiêu?"** — là lõi của toàn hệ thống. Thiết kế theo nguyên tắc **sổ kho** (ledger): mọi thay đổi tồn đều là các dòng ghi sổ bất biến, tồn kho = tổng các dòng ghi.

> Ngữ cảnh quyết định lớn nhất: xem [`docs/adr/0001-stock-movement-ledger.md`](../../adr/0001-stock-movement-ledger.md)

## Tài liệu

| File                                     | Nội dung                                          |
| ---------------------------------------- | ------------------------------------------------- |
| [`model.md`](model.md)                   | Model `StockMovement`, enums, quyết định thiết kế |
| [`api.md`](api.md)                       | Endpoints tồn kho + sổ kho                        |
| [`auth.md`](auth.md)                     | Permissions                                       |
| [`implementation.md`](implementation.md) | Checklist triển khai từng bước                    |
| [`change-log.md`](change-log.md)         | Lịch sử thay đổi thiết kế                         |

## Liên quan

- [`inbound-note/`](../inbound-note/) — phiếu nhập, nguồn ghi sổ đầu tiên
- `outbound-note/`, `stocktake/` — các nguồn ghi sổ tương lai
- [`warehouse/`](../warehouse/) — kho (không có Location, tồn tính theo kho)
