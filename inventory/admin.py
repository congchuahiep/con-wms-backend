from django.contrib import admin

from .models import InboundNote, InboundNoteLine, StockMovement


class InboundNoteLineInline(admin.TabularInline):
    model = InboundNoteLine
    extra = 0
    autocomplete_fields = ["material"]


@admin.register(InboundNote)
class InboundNoteAdmin(admin.ModelAdmin):
    list_display = [
        "number",
        "note_type",
        "status",
        "date",
        "warehouse",
        "supplier",
        "created_by",
    ]
    list_filter = ["note_type", "status", "warehouse"]
    search_fields = ["number", "note"]
    ordering = ["-date", "-id"]
    inlines = [InboundNoteLineInline]
    readonly_fields = [
        "number",
        "status",
        "created_by",
        "voided_by",
        "voided_at",
        "created_at",
        "updated_at",
    ]


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    """Sổ kho bất biến — admin chỉ đọc, không cho sửa/xóa tay."""

    list_display = [
        "id",
        "movement_type",
        "date",
        "material",
        "warehouse",
        "quantity",
        "unit_price",
        "inbound_note",
        "created_by",
    ]
    list_filter = ["movement_type", "warehouse", "date"]
    search_fields = ["material__code", "material__name", "inbound_note__number"]
    ordering = ["-date", "-id"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
