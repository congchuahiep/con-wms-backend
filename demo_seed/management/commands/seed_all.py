from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Chạy toàn bộ seed demo: users → catalog → warehouses → sites → suppliers → notes. "
        "Dùng --reset để xóa phiếu + sổ kho cũ trước khi seed lại."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Xóa toàn bộ phiếu + sổ kho hiện có trước khi seed notes.",
        )

    def handle(self, *args, **options):
        # Dữ liệu nền (idempotent — get_or_create / update_or_create)
        call_command("seed_users")
        call_command("seed_catalog")
        call_command("seed_warehouses")
        call_command("seed_sites")
        call_command("seed_suppliers")
        # Phiếu demo đồ sộ (~55 phiếu, mỗi phiếu 1–10 dòng vật tư)
        call_command("seed_notes", reset=options["reset"])

        self.stdout.write(self.style.SUCCESS("🎉 Seed toàn bộ dữ liệu demo hoàn tất!"))