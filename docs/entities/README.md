# Entities — Domain Model Index

Mỗi entity có một thư mục riêng chứa các file thiết kế (`model.md`, `api.md`, `auth.md`, `implementation.md`, `change-log.md`):

| #   | Entity               | Thư mục                               | Trạng thái     | Django App  |
| --- | -------------------- | ------------------------------------- | -------------- | ----------- |
| 1   | User + Auth          | [`user/`](user/README.md)             | ✅ v1.2 (email-based, ViewSet, register, 5 endpoint) | `iam`     |
| 2   | Warehouse + Location | [`warehouse/`](../warehouse/)         | ⬜ Chưa làm    | `warehouse` |
| 3   | Supplier (NCC)       | [`supplier/`](../supplier/)           | ⬜ Chưa làm    | `supplier`  |
| 4   | Material + Category  | [`material/`](../material/)           | ⬜ Chưa làm    | `catalog`   |
| 5   | Inbound Note         | [`inbound-note/`](../inbound-note/)   | ⬜ Chưa làm    | `inventory` |
| 6   | Outbound Note        | [`outbound-note/`](../outbound-note/) | ⬜ Chưa làm    | `inventory` |
| 7   | Stocktake            | [`stocktake/`](../stocktake/)         | ⬜ Chưa làm    | `stocktake` |
