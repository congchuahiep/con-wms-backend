# Frontend Migration Guide — Đổi tên enum NoteType & MovementType (v1.2)

> **TL;DR**: Tất cả giá trị enum `noteType` và `movementType` đã được **đổi tên cho minh bạch** (tên cũ như "Nhập hoàn trả" gây hiểu nhầm). Dữ liệu cũ đã được migrate — **không mất dữ liệu**. FE cần thay hằng số cũ → mới. Các label tiếng Việt mới đã trả sẵn qua field `*Label` của API.

---

## 1. Breaking Changes Summary

| Enum           | Giá trị cũ         | Giá trị mới                       | Label mới (API trả trong `*Label`)    |
| -------------- | ------------------ | --------------------------------- | ------------------------------------- |
| `noteType`     | `return`           | `return_from_site`                | `Nhập hàng công trường trả lại`       |
| `movementType` | `inbound_purchase` | `inbound_purchase_from_supplier`  | `Nhập kho: mua hàng từ nhà cung cấp`  |
| `movementType` | `inbound_return`   | `inbound_return_from_site`        | `Nhập kho: công trường trả lại hàng`  |
| `movementType` | `outbound_use`     | `outbound_issue_for_use`          | `Xuất kho: cấp phát để sử dụng`       |
| `movementType` | `transfer_out`     | `outbound_transfer_to_warehouse`  | `Xuất kho: điều chuyển sang kho khác` |
| `movementType` | `transfer_in`      | `inbound_transfer_from_warehouse` | `Nhập kho: điều chuyển từ kho khác`   |
| `movementType` | `stocktake_adjust` | `stocktake_adjustment`            | `Điều chỉnh tồn: chênh lệch kiểm kê`  |

Không đổi: `noteType = "purchase"` (label `Mua hàng từ nhà cung cấp`), các giá trị `status` (`draft` / `posted` / `voided`).

**Quy ước đặt tên mới** (để sau này tự hiểu mà không cần tra): giá trị bắt đầu bằng hướng tồn kho — `inbound_` (hàng vào kho, `quantity` dương), `outbound_` (hàng ra khỏi kho, `quantity` âm), `stocktake_` (điều chỉnh tồn, dấu tùy chênh lệch). Phần sau nói rõ lý do + đối tượng liên quan.

---

## 2. Nơi bị ảnh hưởng

### 2.1 Phiếu nhập — `noteType`

- **Request body** (`POST` / `PUT /api/inbound-notes/`):

```jsonc
// Cũ
{ "noteType": "return", ... }

// Mới
{ "noteType": "return_from_site", ... }
```

- **Response** (`GET /api/inbound-notes/`, detail): field `noteType` trả giá trị mới; `noteTypeLabel` trả label mới. **Dùng `noteTypeLabel` để hiển thị.**
- **Filter**: `GET /api/inbound-notes/?note_type=return_from_site`

### 2.2 Sổ kho — `movementType`

- **Response** (`GET /api/stock/movements/`): field `movementType` trả giá trị mới; `movementTypeLabel` trả label mới. **Dùng `movementTypeLabel` để hiển thị.**
- **Filter**: `GET /api/stock/movements/?movement_type=inbound_purchase_from_supplier`

---

## 3. TypeScript types

```ts
// Cũ
type NoteType = "purchase" | "return";
type MovementType =
    | "inbound_purchase"
    | "inbound_return"
    | "outbound_use"
    | "transfer_out"
    | "transfer_in"
    | "stocktake_adjust";

// Mới
type NoteType = "purchase" | "return_from_site";
type MovementType =
    | "inbound_purchase_from_supplier"
    | "inbound_return_from_site"
    | "outbound_issue_for_use"
    | "outbound_transfer_to_warehouse"
    | "inbound_transfer_from_warehouse"
    | "stocktake_adjustment";

interface InboundNote {
    id: number;
    number: string;
    noteType: NoteType; // giá trị enum (key), không hiển thị trực tiếp
    noteTypeLabel: string; // ← dùng để hiển thị
    // ...
}

interface StockMovementItem {
    id: number;
    movementType: MovementType; // giá trị enum (key), không hiển thị trực tiếp
    movementTypeLabel: string; // ← dùng để hiển thị
    quantity: string; // decimal string CÓ DẤU: "+" = nhập, "−" = xuất
    // ...
}
```

---

## 4. Migration guide cho FE

1. **Tìm & thay hằng số** theo bảng mục 1 (7 giá trị).
2. **Không hardcode label tiếng Việt** — luôn dùng field `noteTypeLabel` / `movementTypeLabel` từ API (label đã thay đổi và có thể đổi tiếp trong tương lai).
3. **Chỉ dùng giá trị enum làm key** cho điều kiện logic / filter. Ví dụ:

```ts
// Cũ
if (movement.movementType === "inbound_purchase") {
    /* có đơn giá */
}

// Mới
if (movement.movementType === "inbound_purchase_from_supplier") {
    /* có đơn giá */
}
```

4. **Hiển thị tồn kho có dấu**: `quantity` của dòng sổ kho có dấu `+`/`−` (nhập = dương, xuất = âm). Gợi ý UI: màu xanh cho dương, đỏ cho âm, kèm icon mũi tên ↓↑.
5. **Không có thay đổi nào khác** về response shape, endpoint, phân trang, permission — chỉ đổi giá trị enum và label.

---

## 5. Ví dụ response mới

```json
{
    "id": 12,
    "movementType": "inbound_purchase_from_supplier",
    "movementTypeLabel": "Nhập kho: mua hàng từ nhà cung cấp",
    "date": "2026-08-13",
    "material": { "id": 1, "code": "XM_PCB40", "name": "Xi măng PCB40" },
    "warehouse": {
        "id": 1,
        "code": "KHO_CHINH",
        "name": "Kho chính — Bãi sau"
    },
    "quantity": "100.000",
    "unitPrice": "88000.00",
    "inboundNote": { "id": 3, "number": "PN-20260813-001" },
    "reversalOf": null,
    "reason": "",
    "createdBy": { "id": 2, "email": "thukho@test.com" },
    "createdAt": "2026-08-13T08:30:00+07:00"
}
```

---

## 6. FAQ

- **Dữ liệu cũ có mất không?** Không — migration `0003` đã đổi giá trị cũ → mới trong DB.
- **Gửi giá trị cũ lên server có lỗi không?** Có — giá trị cũ không còn được chấp nhận (400 validation error khi gửi sai enum).
- **4 loại movement chưa dùng** (`outbound_issue_for_use`, `outbound_transfer_to_warehouse`, `inbound_transfer_from_warehouse`, `stocktake_adjustment`): hiện chưa có nghiệp vụ nào sinh ra chúng (phase 2/3), FE có thể define type trước nhưng đừng dựng UI giả.
