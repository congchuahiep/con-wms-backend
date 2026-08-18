from django.core.management.base import BaseCommand
from django.db.models import Sum

from inventory.models import StockMovement


class Command(BaseCommand):
    help = "In tồn kho mẫu (sổ kho đã được seed qua seed_inbound_notes)."

    def handle(self, *args, **options):
        rows = (
            StockMovement.objects.values(
                "warehouse__code", "material__code", "material__name"
            )
            .annotate(total=Sum("quantity"))
            .order_by("warehouse__code", "material__code")
        )

        if not rows:
            self.stdout.write("Chưa có dòng sổ kho — chạy seed_inbound_notes trước.")
            return

        for row in rows:
            self.stdout.write(
                f"  {row['warehouse__code']} | "
                f"{row['material__code']} ({row['material__name']}) | "
                f"tồn: {row['total']}"
            )
        self.stdout.write(self.style.SUCCESS("🎉 Seed stock OK — tồn kho mẫu hiện đúng!"))
