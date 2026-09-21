from decimal import ROUND_HALF_UP, Decimal

from django.db.models import Sum
from rest_framework import serializers

from inventory.models import StockMovement

from .models import Warehouse


class WarehouseSerializer(serializers.ModelSerializer):
    item_count = serializers.SerializerMethodField()
    total_quantity = serializers.SerializerMethodField()
    low_stock = serializers.SerializerMethodField()
    site = serializers.SerializerMethodField()

    class Meta:
        model = Warehouse
        fields = [
            "id",
            "code",
            "name",
            "site",
            "address",
            "note",
            "latitude",
            "longitude",
            "is_active",
            "item_count",
            "total_quantity",
            "low_stock",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {
            "latitude": {"coerce_to_string": False},
            "longitude": {"coerce_to_string": False},
        }

    def get_site(self, obj):
        """Công trường sở hữu kho (null với kho thường)."""
        if obj.site_id is None:
            return None
        return {"id": obj.site_id, "code": obj.site.code, "name": obj.site.name}

    def _balance_rows(self, obj):
        """Tồn theo (mặt hàng) của kho — query 1 lần, cache theo request."""
        cache = self.context.setdefault("_warehouse_balances", {})
        if obj.id not in cache:
            cache[obj.id] = list(
                StockMovement.objects.filter(warehouse=obj)
                .values("material_id")
                .annotate(total=Sum("quantity"))
            )
        return cache[obj.id]

    def get_item_count(self, obj) -> int:
        """Số mặt hàng đang có tồn (balance ≠ 0)."""
        return sum(1 for row in self._balance_rows(obj) if row["total"])

    def get_total_quantity(self, obj) -> float:
        """Tổng tồn kho (chỉ dương) — m3/kg/bao/viên... theo đơn vị từng mặt hàng."""
        return float(
            sum(row["total"] for row in self._balance_rows(obj) if row["total"] > 0)
        )

    def get_low_stock(self, obj) -> int:
        """Số mặt hàng đã hết tồn (balance ≤ 0)."""
        return sum(1 for row in self._balance_rows(obj) if row["total"] <= 0)

    def to_internal_value(self, data):
        """
        Truncate lat/lng về 9 chữ số thập phân trước khi model validation,
        phòng trường hợp Google Maps trả về floating-point cực dài.
        """
        data = dict(data)
        precision = Decimal("0.000000001")
        for field in ("latitude", "longitude"):
            if field in data and data[field] not in (None, ""):
                data[field] = Decimal(str(data[field])).quantize(
                    precision, rounding=ROUND_HALF_UP
                )
        return super().to_internal_value(data)
