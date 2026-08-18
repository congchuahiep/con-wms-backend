# Entities — Domain Model Index

Mỗi entity có một thư mục riêng chứa các file thiết kế (`model.md`, `api.md`, `auth.md`, `implementation.md`, `change-log.md`):

| #   | Entity               | Thư mục                                     | Trạng thái                                                             | Django App  |
| --- | -------------------- | ------------------------------------------- | ---------------------------------------------------------------------- | ----------- |
| 1   | User + Auth          | [`user/`](user/README.md)                   | ✅ v1.2 (email-based, ViewSet, register, 5 endpoint)                   | `iam`       |
| 2   | Warehouse            | [`warehouse/`](warehouse/README.md)         | ✅ v1.3 (9 fields, 5 endpoints, 8 tests)                               | `warehouse` |
| 3   | Supplier (NCC)       | [`supplier/`](supplier/README.md)           | ✅ v1.0 (12 fields, 5 endpoints, 8 tests)                              | `supplier`  |
| 4   | Material + Category  | [`material/`](material/README.md)           | ✅ v1.2 (Material + Category; Unit đã tách riêng)                      | `catalog`   |
| 5   | Unit + Conversion    | [`unit/`](unit/README.md)                   | ✅ Done (conversionType, reverse virtual, partial unique, hard delete) | `catalog`   |
| 6   | Inbound Note         | [`inbound-note/`](inbound-note/README.md)   | ✅ v2.0 (draft→posted→voided, 7 endpoints, 31 tests)                   | `inventory` |
| 7   | Outbound Note        | [`outbound-note/`](outbound-note/README.md) | ⬜ Chưa làm                                                            | `inventory` |
| 8   | Stocktake            | [`stocktake/`](stocktake/README.md)         | ⬜ Chưa làm                                                            | `stocktake` |
| 9   | Stock (Sổ kho & Tồn) | [`stock/`](stock/README.md)                 | ✅ v1.0 (StockMovement ledger, 2 endpoint read-only, ADR-0001)         | `inventory` |
