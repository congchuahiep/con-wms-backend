from datetime import date

from django.core.management.base import BaseCommand

from catalog.models import Material
from iam.models import User
from inventory.models import OutboundNote, OutboundNoteLine
from sites.models import Site
from warehouse.models import Warehouse


class Command(BaseCommand):
    help = "Seed 1 phiếu xuất cấp + 1 phiếu điều chuyển và tự chốt."
    def handle(self, *args, **options):
        wh_chinh = Warehouse.objects.filter(code="KHO_CHINH").first()
        wh_phu = Warehouse.objects.filter(code="KHO_PHU").first()
        site = Site.objects.filter(code="CT_RG").first()
        user = User.objects.filter(role="admin").first()
        xm = Material.objects.filter(code="XM-HT-PCB40").first() or Material.objects.first()
        cat = Material.objects.filter(code="CAT-VANG").first() or Material.objects.last()
        if not all([wh_chinh, wh_phu, site, user, xm]):
            self.stdout.write(self.style.ERROR("Thiếu dữ liệu nền (warehouse/site/material/user)"))
            return
        notes = [
            {"number":"PX-20260803-001","note_type":OutboundNote.Type.ISSUE_FOR_USE,"date":date(2026,8,3),"warehouse":wh_chinh,"site":site,"to_warehouse":None,"note":"Cấp xi măng cho CT Rạch Giá","lines":[{"material":xm,"quantity":"20"},{"material":cat,"quantity":"1"}]},
            {"number":"PX-20260803-002","note_type":OutboundNote.Type.TRANSFER,"date":date(2026,8,3),"warehouse":wh_chinh,"site":None,"to_warehouse":wh_phu,"note":"Điều chuyển sang kho phụ","lines":[{"material":xm,"quantity":"10"}]},
        ]
        for item in notes:
            number=item.pop("number"); lines=item.pop("lines")
            if OutboundNote.objects.filter(number=number).exists():
                self.stdout.write(self.style.WARNING(f"⏭ Bỏ qua {number}"))
                continue
            note=OutboundNote.objects.create(number=number, created_by=user, **item)
            for idx,l in enumerate(lines,1):
                OutboundNoteLine.objects.create(outbound_note=note, line_no=idx, **l)
            try:
                note.post(user)
                self.stdout.write(self.style.SUCCESS(f"✅ {note} chốt ok"))
            except Exception as e:  # noqa: BLE001 - seed tiếp tục dù 1 phiếu lỗi
                self.stdout.write(self.style.ERROR(f"❌ {number} lỗi chốt: {e}"))
