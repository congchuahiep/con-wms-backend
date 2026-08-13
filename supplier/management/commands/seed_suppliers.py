from django.core.management.base import BaseCommand

from supplier.models import Supplier


class Command(BaseCommand):
    help = "Seed 2 nhà cung cấp mẫu"

    def handle(self, *args, **options):
        data = [
            {
                "code": "NCC001",
                "name": "Công ty TNHH Vật Liệu Xây Dựng ABC",
                "tax_code": "0123456789",
                "contact_person": "Anh Tuấn — quản lý bán hàng",
                "phone": "0903123456",
                "email": "sales@abc-vlxd.com",
                "address": "Số 45, đường Nguyễn Huệ, TP. HCM",
                "note": "Giao hàng thứ 3-5-7, giá tốt nhưng hay giao trễ",
            },
            {
                "code": "NCC002",
                "name": "Đại lý Sắt Thép Miền Tây",
                "tax_code": "0987654321",
                "contact_person": "Chị Hương",
                "phone": "0918123456",
                "email": "huong@satthepmientay.com",
                "address": "Quốc lộ 1A, huyện Bến Lức, Long An",
                "note": "Giá sắt tốt nhất khu vực",
            },
        ]

        for item in data:
            obj, created = Supplier.objects.get_or_create(
                code=item["code"], defaults=item
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Đã tạo: {obj}")
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f"⏭ Đã tồn tại, bỏ qua: {obj}")
                )

        self.stdout.write(self.style.SUCCESS("🎉 Seed suppliers hoàn tất!"))
