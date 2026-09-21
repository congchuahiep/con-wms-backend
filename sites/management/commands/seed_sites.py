from django.core.management.base import BaseCommand

from catalog.models import Material
from sites.models import Site, SiteMaterialRequirement
from sites.services import ensure_site_warehouse
from warehouse.models import Warehouse


class Command(BaseCommand):
    help = "Tạo dữ liệu mẫu cho Site — 5 công trường."

    def handle(self, *args, **options):
        data = [
            {
                "code": "CT_RG",
                "name": "Công trường cầu Rạch Giá",
                "manager": "Kỹ sư Trần Văn Hùng",
                "phone": "0901123456",
                "address": "TP. Rạch Giá, Kiên Giang",
                "note": "Cầu qua kênh, thi công 2 mũi từ 2 đầu cầu",
            },
            {
                "code": "CT_KE_SONG_BE",
                "name": "Kè Sông Bé",
                "manager": "Kỹ sư Lê Thị Mai",
                "phone": "0902123456",
                "address": "Huyện Dầu Tiếng, Bình Dương",
                "note": "Kè bê tông dài 820m, đã gia cố xong phần móng",
            },
            {
                "code": "CT_ND",
                "name": "Nhà dân — Nhà chú Bảy",
                "manager": "Chú Bảy",
                "phone": "0983123456",
                "address": "Huyện Gò Công, Tiền Giang",
                "note": "Nhà cấp 4, xây mới + sửa chữa phần mái",
            },
            {
                "code": "CT_NHA_XUONG",
                "name": "Nhà xưởng Cơ khí Hoàng Gia",
                "manager": "Kỹ sư Phạm Minh Tuấn",
                "phone": "0904123456",
                "address": "KCN Long An",
                "note": "Xưởng khung thép 2.400m², đang đổ nền bê tông",
            },
            {
                "code": "CT_TRUONG_HOC",
                "name": "Trường mầm non Hoa Sen",
                "manager": "Kỹ sư Nguyễn Thị Lan",
                "phone": "0905123456",
                "address": "Huyện Cần Giuộc, Long An",
                "note": "Công trình dân lập, 2 tầng, 6 phòng học",
            },
        ]

        for item in data:
            site, created = Site.objects.update_or_create(
                code=item["code"],
                defaults=item,
            )
            ensure_site_warehouse(site)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Đã tạo công trường: {site}"))
            else:
                self.stdout.write(self.style.WARNING(f"Công trường đã tồn tại: {site}"))

        # Seed chỉ giữ 5 công trường — dọn công trường mẫu cũ (CT_DUONG_NT) nếu còn sót
        stale = Site.objects.filter(code="CT_DUONG_NT").first()
        if stale:
            stale.status = Site.Status.INACTIVE
            stale.save()
            stale_wh = getattr(stale, "warehouse", None)
            if stale_wh:
                stale_wh.is_active = False
                stale_wh.save()
            self.stdout.write(
                self.style.WARNING(f"Công trường cũ {stale} đã vô hiệu hóa (kèm kho công trường).")
            )

        # Định mức vật tư mẫu cho một vài công trường
        requirements = {
            "CT_RG": [("XM-HT-PCB40", "100"), ("GACH-ONG", "20000")],
            "CT_NHA_XUONG": [("THEP-D10", "5000"), ("DA-1X2", "120")],
        }
        for code, lines in requirements.items():
            site = Site.objects.filter(code=code).first()
            if site is None:
                continue
            for material_code, quantity in lines:
                material = Material.objects.filter(code=material_code).first()
                if material is None:
                    continue
                SiteMaterialRequirement.objects.update_or_create(
                    site=site, material=material, defaults={"quantity": quantity}
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"🎉 Seed sites hoàn tất — {Site.objects.filter(status=Site.Status.ACTIVE).count()} công trường"
                f" + {Warehouse.objects.filter(site__isnull=False, is_active=True).count()} kho công trường"
                f" + {SiteMaterialRequirement.objects.count()} dòng định mức."
            )
        )