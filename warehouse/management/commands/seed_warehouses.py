from django.core.management.base import BaseCommand
from django.db.models.deletion import ProtectedError

from warehouse.models import Warehouse


class Command(BaseCommand):
    help = "Seed 2 nhà kho mẫu: 1 kho chính + 1 kho phụ."

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
            warehouse, created = Warehouse.objects.update_or_create(
                code=item["code"],
                defaults=item,
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Đã tạo kho: {warehouse}"))
            else:
                self.stdout.write(self.style.WARNING(f"Kho đã tồn tại: {warehouse}"))

        # Seed chỉ giữ 2 kho trung tâm — dọn kho mẫu cũ (KHO_CAT_DA) nếu còn sót
        for stale in Warehouse.objects.filter(code="KHO_CAT_DA"):
            try:
                stale.delete()
            except ProtectedError:
                stale.is_active = False
                stale.save()
                self.stdout.write(
                    self.style.WARNING(f"Kho cũ {stale} bị khóa bởi dữ liệu — đã vô hiệu hóa.")
                )

        self.stdout.write(
            self.style.SUCCESS("🎉 Seed warehouses hoàn tất — 2 kho trung tâm.")
        )