from django_filters import rest_framework as filters

from .models import InboundNote, OutboundNote, StockMovement, StocktakeNote


class InboundNoteFilter(filters.FilterSet):
    date_from = filters.DateFilter(field_name="date", lookup_expr="gte")
    date_to = filters.DateFilter(field_name="date", lookup_expr="lte")

    class Meta:
        model = InboundNote
        fields = ["note_type", "status", "warehouse", "supplier", "site"]


class OutboundNoteFilter(filters.FilterSet):
    date_from = filters.DateFilter(field_name="date", lookup_expr="gte")
    date_to = filters.DateFilter(field_name="date", lookup_expr="lte")

    class Meta:
        model = OutboundNote
        fields = ["note_type", "status", "warehouse", "site", "to_warehouse"]


class StocktakeNoteFilter(filters.FilterSet):
    date_from = filters.DateFilter(field_name="date", lookup_expr="gte")
    date_to = filters.DateFilter(field_name="date", lookup_expr="lte")

    class Meta:
        model = StocktakeNote
        fields = ["status", "warehouse"]


class StockMovementFilter(filters.FilterSet):
    date_from = filters.DateFilter(field_name="date", lookup_expr="gte")
    date_to = filters.DateFilter(field_name="date", lookup_expr="lte")

    class Meta:
        model = StockMovement
        fields = ["material", "warehouse", "movement_type", "inbound_note", "outbound_note", "stocktake_note"]


class StockBalanceFilter(filters.FilterSet):
    """Filter cho GET /api/stock/ — chạy trên queryset values() + aggregate."""

    warehouse = filters.NumberFilter(field_name="warehouse_id")
    material = filters.NumberFilter(field_name="material_id")
    category = filters.NumberFilter(field_name="material__category_id")
    has_stock = filters.BooleanFilter(method="filter_has_stock")

    def filter_has_stock(self, queryset, name, value):
        if value:
            return queryset.filter(quantity__gt=0)
        return queryset.filter(quantity=0)
