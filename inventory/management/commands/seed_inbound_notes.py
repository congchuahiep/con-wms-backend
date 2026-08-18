from datetime import date

from django.core.management.base import BaseCommand

from catalog.models import Material
from iam.models import User
from inventory.models import InboundNote, InboundNoteLine
from supplier.models import Supplier
from warehouse.models import Warehouse


class Command(BaseCommand):
    help = "Seed 2 phiếu nhập mẫu (1 nhập mua + 1 nhập hàng công trường trả lại) và tự chốt."

    def handle(self, *args, **options):
        warehouse = Warehouse.objects.filter(code="KHO_CHINH").first()
        supplier = Supplier.objects.filter(code="NCC001").first()
        user = User.objects.filter(role="admin").first()
        xm = Material.objects.filter(code="XM-HT-PCB40").first()
        cat = Material.objects.filter(code="CAT-VANG").first()

        missing = []
        if not warehouse:
            missing.append("Warehouse KHO_CHINH (chạy seed_warehouses)")
        if not supplier:
            missing.append("Supplier NCC001 (chạy seed_suppliers)")
        if not user:
            missing.append("User admin (tạo qua /api/auth/register/)")
        if not xm or not cat:
            missing.append("Materials (chạy seed_catalog)")
        if missing:
            self.stdout.write(self.style.ERROR("Thiếu dữ liệu nền:"))
            for item in missing:
                self.stdout.write(f"  - {item}")
            return

        notes = [
            {
                "number": "PN-20260801-001",
                "note_type": InboundNote.Type.PURCHASE,
                "date": date(2026, 8, 1),
                "warehouse": warehouse,
                "supplier": supplier,
                "note": "Nhập xi măng + cát cho công trình cầu Rạch Giá",
                "lines": [
                    {
                        "material": xm,
                        "quantity": "100",
                        "unit_price": "88000",
                        "line_no": 1,
                        "note": "Bao 50kg",
                    },
                    {
                        "material": cat,
                        "quantity": "5.5",
                        "unit_price": "350000",
                        "line_no": 2,
                        "note": "",
                    },
                ],
            },
            {
                "number": "PN-20260802-001",
                "note_type": InboundNote.Type.RETURN_FROM_SITE,
                "date": date(2026, 8, 2),
                "warehouse": warehouse,
                "supplier": None,
                "note": "Công trường trả lại xi măng thừa",
                "lines": [
                    {
                        "material": xm,
                        "quantity": "10",
                        "unit_price": "88000",
                        "line_no": 1,
                        "note": "",
                    },
                ],
            },
        ]

        for item in notes:
            number = item.pop("number")
            lines = item.pop("lines")
            if InboundNote.objects.filter(number=number).exists():
                self.stdout.write(self.style.WARNING(f"⏭ Đã tồn tại, bỏ qua: {number}"))
                continue

            note = InboundNote.objects.create(number=number, created_by=user, **item)
            for line in lines:
                InboundNoteLine.objects.create(inbound_note=note, **line)
            note.post(user)
            self.stdout.write(self.style.SUCCESS(f"✅ Đã tạo + chốt: {note}"))

        self.stdout.write(self.style.SUCCESS("🎉 Seed inbound notes hoàn tất!"))
