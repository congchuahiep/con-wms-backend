from django.contrib import admin

from .models import Material, MaterialCategory, Unit, UnitConversion


@admin.register(MaterialCategory)
class MaterialCategoryAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "color", "parent", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["code", "name"]


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["code", "name"]


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "category", "unit", "is_active"]
    list_filter = ["is_active", "category"]
    search_fields = ["code", "name"]


@admin.register(UnitConversion)
class UnitConversionAdmin(admin.ModelAdmin):
    list_display = ["from_unit", "to_unit", "factor", "material", "is_active"]
    list_filter = ["is_active", "from_unit"]
    search_fields = ["from_unit__code", "to_unit__code"]
