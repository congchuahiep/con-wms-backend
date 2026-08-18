"""Sinh số phiếu — logic chốt/hủy phiếu nằm ở `BaseNote.post()` / `void()`.

Vòng đời phiếu (nháp → chốt → hủy) được gom trong `inventory.models.BaseNote`
để mọi loại phiếu (Inbound, Outbound, Stocktake) dùng chung. Mỗi loại chỉ
cung cấp 2 hook sinh dòng sổ kho riêng.
Xem docs/entities/stock/model.md — ADR-0001.
"""

from .models import InboundNote


def generate_inbound_note_number(note_date):
    """Sinh số phiếu `PN-YYYYMMDD-NNN` — NNN là sequence trong ngày."""
    prefix = f"PN-{note_date:%Y%m%d}-"
    last = (
        InboundNote.objects.filter(number__startswith=prefix)
        .order_by("-number")
        .values_list("number", flat=True)
        .first()
    )
    seq = int(last.rsplit("-", 1)[-1]) + 1 if last else 1
    return f"{prefix}{seq:03d}"
