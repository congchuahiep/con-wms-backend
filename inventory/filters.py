from django_filters import rest_framework as filters

from .models import InboundNote, StockMovement


class InboundNoteFilter(filters.FilterSet):
    date_from = filters.DateFilter(field_name="date", lookup_expr="gte")
    date_to = filters.DateFilter(field_name="date", lookup_expr="lte")

    class Meta:
        model = InboundNote
        fields = ["note_type", "status", "warehouse", "supplier"]


class StockMovementFilter(filters.FilterSet):
    date_from = filters.DateFilter(field_name="date", lookup_expr="gte")
    date_to = filters.DateFilter(field_name="date", lookup_expr="lte")

    class Meta:
        model = StockMovement
        fields = ["material", "warehouse", "movement_type", "inbound_note"]


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
