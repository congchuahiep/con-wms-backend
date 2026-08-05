from decimal import ROUND_HALF_UP, Decimal

from rest_framework import serializers

from .models import Warehouse


class WarehouseSerializer(serializers.ModelSerializer):
    item_count = serializers.SerializerMethodField()
    total_quantity = serializers.SerializerMethodField()
    low_stock = serializers.SerializerMethodField()

    class Meta:
        model = Warehouse
        fields = [
            "id",
            "code",
            "name",
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

    def get_item_count(self, obj) -> int:
        return 0  # TODO: implement khi có model Vật tư

    def get_total_quantity(self, obj) -> int:
        return 0  # TODO: implement khi có model Vật tư

    def get_low_stock(self, obj) -> int:
        return 0  # TODO: implement khi có model Vật tư

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
