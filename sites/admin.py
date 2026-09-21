from django.contrib import admin

from .models import Site, SiteMaterialRequirement


class SiteMaterialRequirementInline(admin.TabularInline):
    model = SiteMaterialRequirement
    extra = 0
    autocomplete_fields = ["material"]


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "manager", "status", "settled_at")
    list_filter = ("status",)
    search_fields = ("code", "name")
    inlines = [SiteMaterialRequirementInline]


@admin.register(SiteMaterialRequirement)
class SiteMaterialRequirementAdmin(admin.ModelAdmin):
    list_display = ("site", "material", "quantity")
    list_filter = ("site",)
    search_fields = ("site__code", "site__name", "material__code", "material__name")
    autocomplete_fields = ["site", "material"]