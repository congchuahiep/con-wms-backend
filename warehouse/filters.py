from django.db.models import Q
from django_filters import rest_framework as filters

from .models import Warehouse


class WarehouseFilter(filters.FilterSet):
    search = filters.CharFilter(method="filter_search")
    is_active = filters.BooleanFilter()

    class Meta:
        model = Warehouse
        fields = ["is_active"]

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(code__icontains=value) | Q(name__icontains=value)
        ).distinct()
