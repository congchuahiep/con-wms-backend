from datetime import date

from django.core.management.base import BaseCommand

from catalog.models import Material
from iam.models import User
from inventory.models import StocktakeLine, StocktakeNote
from warehouse.models import Warehouse


class Command(BaseCommand):
    help = "Seed 1 phiếu kiểm kê mẫu với vài dòng lệch và tự chốt."
    def handle(self, *args, **options):
        wh = Warehouse.objects.filter(code="KHO_CHINH").first()
        user = User.objects.filter(role="admin").first()
        xm = Material.objects.filter(code="XM-HT-PCB40").first() or Material.objects.first()
        cat = Material.objects.filter(code="CAT-VANG").first() or Material.objects.last()
        if not all([wh, user, xm]):
            self.stdout.write(self.style.ERROR("Thiếu dữ liệu nền"))
            return
        number="PK-20260804-001"
        if StocktakeNote.objects.filter(number=number).exists():
            self.stdout.write(self.style.WARNING(f"⏭ Bỏ qua {number}"))
            return
        note=StocktakeNote.objects.create(number=number, date=date(2026,8,4), warehouse=wh, created_by=user, note="Kiểm kê sau xuất")
        StocktakeLine.objects.create(stocktake_note=note, material=xm, difference="-2", reason="2 bao rách vỡ", line_no=1)
        StocktakeLine.objects.create(stocktake_note=note, material=cat, difference="0.5", reason="Thừa sau cân lại", line_no=2)
        try:
            note.post(user)
            self.stdout.write(self.style.SUCCESS(f"✅ {note} chốt ok"))
        except Exception as e:  # noqa: BLE001 - seed tiếp tục dù 1 phiếu lỗi
            self.stdout.write(self.style.ERROR(f"❌ Lỗi chốt: {e}"))
