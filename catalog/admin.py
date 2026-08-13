from django.contrib import admin

from .models import Material, MaterialCategory, Unit, UnitConversion


@admin.register(MaterialCategory)
class MaterialCategoryAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "color", "parent"]
    list_filter = []
    search_fields = ["code", "name"]


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ["code", "name"]
    list_filter = []
    search_fields = ["code", "name"]


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "category", "unit"]
    list_filter = ["category"]
    search_fields = ["code", "name"]


@admin.register(UnitConversion)
class UnitConversionAdmin(admin.ModelAdmin):
    list_display = ["from_unit", "to_unit", "factor", "material"]
    list_filter = ["from_unit"]
    search_fields = ["from_unit__code", "to_unit__code"]
