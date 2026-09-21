# Data migration: chuyển dữ liệu `is_active` (bool) sang `status` (enum).
#
# - is_active=True  → status="active"
# - is_active=False → status="inactive"
#
# `status` đã tồn tại (0002, default "active"); `is_active` chưa xóa —
# bước xóa cột nằm ở migration 0004.

from django.db import migrations


def migrate_is_active_to_status(apps, schema_editor):
    Site = apps.get_model("sites", "Site")
    for site in Site.objects.all().iterator():
        if not site.is_active:
            site.status = "inactive"
            site.save(update_fields=["status"])
    # Dòng is_active=True giữ nguyên default "active" — không cần ghi.


def reverse_migrate_status_to_is_active(apps, schema_editor):
    Site = apps.get_model("sites", "Site")
    for site in Site.objects.all().iterator():
        site.is_active = site.status != "inactive"
        site.save(update_fields=["is_active"])


class Migration(migrations.Migration):

    dependencies = [
        ("sites", "0002_site_settled_at_site_settled_by_site_status_and_more"),
    ]

    operations = [
        migrations.RunPython(
            migrate_is_active_to_status,
            reverse_migrate_status_to_is_active,
        ),
    ]