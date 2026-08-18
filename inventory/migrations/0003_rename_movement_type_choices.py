"""Đổi giá trị enum cũ → mới cho note_type và movement_type.

Tên cũ gây nhầm lẫn (vd "inbound_return" / "Nhập hoàn trả" đọc như trả hàng
cho NCC). Xem docs/entities/stock/change-log.md v1.2.
"""

from django.db import migrations

NOTE_TYPE_MAP = {
    "return": "return_from_site",
}

MOVEMENT_TYPE_MAP = {
    "inbound_purchase": "inbound_purchase_from_supplier",
    "inbound_return": "inbound_return_from_site",
    "outbound_use": "outbound_issue_for_use",
    "transfer_out": "outbound_transfer_to_warehouse",
    "transfer_in": "inbound_transfer_from_warehouse",
    "stocktake_adjust": "stocktake_adjustment",
}


def rename_choices(apps, schema_editor, model_name, field_name, mapping):
    Model = apps.get_model("inventory", model_name)
    for old, new in mapping.items():
        Model.objects.filter(**{field_name: old}).update(**{field_name: new})


def forwards(apps, schema_editor):
    rename_choices(apps, schema_editor, "InboundNote", "note_type", NOTE_TYPE_MAP)
    rename_choices(
        apps, schema_editor, "StockMovement", "movement_type", MOVEMENT_TYPE_MAP
    )


def backwards(apps, schema_editor):
    reverse_note = {v: k for k, v in NOTE_TYPE_MAP.items()}
    reverse_movement = {v: k for k, v in MOVEMENT_TYPE_MAP.items()}
    rename_choices(apps, schema_editor, "InboundNote", "note_type", reverse_note)
    rename_choices(
        apps, schema_editor, "StockMovement", "movement_type", reverse_movement
    )


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0002_alter_inboundnote_note_type_and_more"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
