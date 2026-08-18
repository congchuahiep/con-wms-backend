# Authentication & Authorization — Stock

## 1. Permissions

Sổ kho là dữ liệu **đọc** cho mọi người đã đăng nhập (kế toán cần xem để đối chiếu). **Không ai** — kể cả admin — có quyền ghi trực tiếp vào sổ kho.

| Endpoint                         | Permission Class  | Ghi chú                                       |
| -------------------------------- | ----------------- | --------------------------------------------- |
| `GET /api/stock/`                | `IsAuthenticated` | Mọi role xem tồn kho                          |
| `GET /api/stock/movements/`      | `IsAuthenticated` | Mọi role xem sổ kho (kế toán tra lịch sử NCC) |
| `POST/PUT/DELETE` (mọi endpoint) | —                 | Không tồn tại — 405                           |

## 2. Ai được làm thay đổi tồn kho (gián tiếp)

Việc ghi sổ kho chỉ xảy ra qua các hành động trên **phiếu**:

| Hành động                         | Ai được làm                     | Entity      |
| --------------------------------- | ------------------------------- | ----------- |
| Chốt phiếu nhập (→ dòng +)        | Thủ kho + admin                 | InboundNote |
| Hủy phiếu nhập (→ dòng ngược dấu) | Thủ kho + admin, bắt buộc lý do | InboundNote |
| Chốt phiếu xuất / kiểm kê         | Thủ kho + admin                 | Tương lai   |

## 3. Custom Permissions

Không cần custom permission mới — dùng lại từ `iam/permissions.py`:

- `IsAuthenticated` — GET sổ kho + tồn kho

## 4. ViewSet permission mapping

```python
# inventory/views.py
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated


class StockBalanceViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    # queryset = aggregate theo (warehouse, material)


class StockMovementViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = StockMovement.objects.filter(reversal_of__isnull=True) \
        .select_related("material", "warehouse", "inbound_note", "created_by")
```

## 5. JWT Claims

Không áp dụng — không cần nhúng thông tin vào JWT token.
