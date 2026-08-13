from django.db.models import Q
from django_filters import rest_framework as filters

from .models import Supplier


class SupplierFilter(filters.FilterSet):
    search = filters.CharFilter(method="filter_search")
    is_active = filters.BooleanFilter()

    class Meta:
        model = Supplier
        fields = ["is_active"]

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(code__icontains=value) | Q(name__icontains=value)
        ).distinct()
