from django.contrib import admin

from .models import Supplier


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "tax_code", "contact_person", "phone", "is_active", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["code", "name", "tax_code", "contact_person", "phone"]
    ordering = ["code"]
