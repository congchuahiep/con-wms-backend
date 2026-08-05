from django.core.management.base import BaseCommand

from warehouse.models import Warehouse


class Command(BaseCommand):
    help = "Tạo dữ liệu mẫu cho Warehouse"

    def handle(self, *args, **options):
        data = [
            {
                "code": "KHO_CHINH",
                "name": "Kho chính — Bãi sau",
                "address": "Số 12, đường A, xã B",
                "note": "Kho chính — nền bê tông, mái tôn, có cửa cuốn",
                "latitude": 10.762622,
                "longitude": 106.660172,
            },
            {
                "code": "KHO_PHU",
                "name": "Kho phụ — Gần cổng",
                "address": "Đường nội bộ công ty",
                "note": "Kho phụ — nền đất, che bạt, chỉ chứa vật liệu nhẹ",
                "latitude": 10.772622,
                "longitude": 106.670172,
            },
        ]

        for item in data:
            warehouse, created = Warehouse.objects.get_or_create(
                code=item["code"],
                defaults=item,
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f"Đã tạo kho: {warehouse}")
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f"Kho đã tồn tại: {warehouse}")
                )
