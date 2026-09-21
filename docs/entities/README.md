# Entities — Domain Model Index

Mỗi entity có một thư mục riêng chứa các file thiết kế (`model.md`, `api.md`, `auth.md`, `implementation.md`, `change-log.md`):

| #   | Entity                           | Thư mục                                       | Trạng thái                                                                     | Django App            |
| --- | -------------------------------- | --------------------------------------------- | ------------------------------------------------------------------------------ | --------------------- |
| 1   | User + Auth                      | [`user/`](user/README.md)                     | ✅ v1.2 (email-based, ViewSet, register, 5 endpoint)                           | `iam`                 |
| 2   | Warehouse                        | [`warehouse/`](warehouse/README.md)           | ✅ v1.3 (9 fields, 5 endpoints, 8 tests)                                       | `warehouse`           |
| 3   | Supplier (NCC)                   | [`supplier/`](supplier/README.md)             | ✅ v1.0 (12 fields, 5 endpoints, 8 tests)                                      | `supplier`            |
| 4   | Site (Công trường)               | [`site/`](site/README.md)                     | 📝 v0.1 design xong — chờ duyệt (chưa code)                                    | `sites`               |
| 5   | Material + Category              | [`material/`](material/README.md)             | ✅ v1.2 (Material + Category; Unit đã tách riêng)                              | `catalog`             |
| 6   | Unit + Conversion                | [`unit/`](unit/README.md)                     | ✅ Done (conversionType, reverse virtual, partial unique, hard delete)         | `catalog`             |
| 7   | Inbound Note                     | [`inbound-note/`](inbound-note/README.md)     | ✅ v2.0 (draft→posted→voided, 7 endpoints, 31 tests)                           | `inventory`           |
| 8   | Outbound Note                    | [`outbound-note/`](outbound-note/README.md)   | 📝 v0.1 design xong — chờ duyệt (chưa code)                                    | `inventory`           |
| 9   | Stocktake                        | [`stocktake/`](stocktake/README.md)           | 📝 v0.1 design xong — chờ duyệt (chưa code)                                    | `inventory`           |
| 10  | Stock (Sổ kho & Tồn)             | [`stock/`](stock/README.md)                   | ✅ v1.4 (StockMovement ledger + BaseNote, 2 endpoint read-only, ADR-0001)      | `inventory`           |
| 11  | Site Warehouse (Kho Công Trường) | [`site-warehouse/`](site-warehouse/README.md) | ✅ v1.1 triển khai xong (Warehouse.site 1-1, auto-create khi tạo Site, 54 tests pass) | `warehouse` + `sites` |
| 12  | Site Material Requirement (Định mức vật tư CT) | [`site-material-requirement/`](site-material-requirement/README.md) | 📝 v0.1 design xong — chờ duyệt (chưa code) | `sites` + `inventory` + `warehouse` |
