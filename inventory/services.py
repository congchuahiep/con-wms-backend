"""Sinh số phiếu — logic chốt/hủy phiếu nằm ở `BaseNote.post()` / `void()`."""

from .models import InboundNote, OutboundNote, StocktakeNote


def generate_inbound_note_number(note_date):
    prefix = f"PN-{note_date:%Y%m%d}-"
    last = InboundNote.objects.filter(number__startswith=prefix).order_by("-number").values_list("number", flat=True).first()
    seq = int(last.rsplit("-", 1)[-1]) + 1 if last else 1
    return f"{prefix}{seq:03d}"


def generate_outbound_note_number(note_date):
    prefix = f"PX-{note_date:%Y%m%d}-"
    last = OutboundNote.objects.filter(number__startswith=prefix).order_by("-number").values_list("number", flat=True).first()
    seq = int(last.rsplit("-", 1)[-1]) + 1 if last else 1
    return f"{prefix}{seq:03d}"


def generate_stocktake_note_number(note_date):
    prefix = f"PK-{note_date:%Y%m%d}-"
    last = StocktakeNote.objects.filter(number__startswith=prefix).order_by("-number").values_list("number", flat=True).first()
    seq = int(last.rsplit("-", 1)[-1]) + 1 if last else 1
    return f"{prefix}{seq:03d}"
