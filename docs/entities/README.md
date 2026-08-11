# Entities — Domain Model Index

Mỗi entity có một thư mục riêng chứa các file thiết kế (`model.md`, `api.md`, `auth.md`, `implementation.md`, `change-log.md`):

| #   | Entity              | Thư mục                               | Trạng thái                                           | Django App  |
| --- | ------------------- | ------------------------------------- | ---------------------------------------------------- | ----------- |
| 1   | User + Auth         | [`user/`](user/README.md)             | ✅ v1.2 (email-based, ViewSet, register, 5 endpoint) | `iam`       |
| 2   | Warehouse           | [`warehouse/`](warehouse/README.md)   | ✅ v1.3 (9 fields, 5 endpoints, 8 tests)             | `warehouse` |
| 3   | Supplier (NCC)      | [`supplier/`](../supplier/)           | ⬜ Chưa làm                                          | `supplier`  |
| 4   | Material + Category | [`material/`](material/README.md)     | ✅ v1.2 (Material + Category; Unit đã tách riêng)     | `catalog`   |
| 5   | Unit + Conversion   | [`unit/`](unit/README.md)             | 🔵 Đã thiết kế (v1.3), chờ duyệt                      | `catalog`   |
| 6   | Inbound Note        | [`inbound-note/`](../inbound-note/)   | ⬜ Chưa làm                                          | `inventory` |
| 7   | Outbound Note       | [`outbound-note/`](../outbound-note/) | ⬜ Chưa làm                                          | `inventory` |
| 8   | Stocktake           | [`stocktake/`](../stocktake/)         | ⬜ Chưa làm                                          | `stocktake` |
