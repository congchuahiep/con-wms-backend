from decimal import Decimal

from rest_framework import serializers

from catalog.models import Material
from catalog.serializers import SimpleMaterialSerializer
from inventory.serializers import SimpleUserSerializer
from warehouse.models import Warehouse

from .models import Site, SiteMaterialRequirement


class SiteSerializer(serializers.ModelSerializer):
    warehouse = serializers.SerializerMethodField()
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    settled_by = SimpleUserSerializer(read_only=True, allow_null=True)

    class Meta:
        model = Site
        fields = [
            "id",
            "code",
            "name",
            "manager",
            "phone",
            "address",
            "note",
            "status",
            "status_label",
            "settled_at",
            "settled_by",
            "warehouse",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_warehouse(self, obj):
        """Kho công trường liên kết (tự động tạo khi tạo site)."""
        warehouse = getattr(obj, "warehouse", None)
        if warehouse is None:
            return None
        return {"id": warehouse.id, "code": warehouse.code, "name": warehouse.name}


class SiteRequirementRowSerializer(serializers.Serializer):
    """Bảng so sánh định mức vs tồn kho — decimals dạng chuỗi (giống StockBalance)."""

    material = SimpleMaterialSerializer(read_only=True)
    required_quantity = serializers.DecimalField(
        max_digits=14, decimal_places=3, allow_null=True
    )
    balance = serializers.DecimalField(max_digits=14, decimal_places=3)
    status = serializers.ChoiceField(
        choices=["sufficient", "insufficient", "not_in_plan"]
    )
    default_return_quantity = serializers.DecimalField(
        max_digits=14, decimal_places=3
    )
    note = serializers.CharField(allow_null=True)


class SiteMaterialRequirementSerializer(serializers.ModelSerializer):
    """Output dòng định mức (sau khi PUT) — không kèm tồn kho."""

    material = SimpleMaterialSerializer(read_only=True)

    class Meta:
        model = SiteMaterialRequirement
        fields = ["id", "material", "quantity", "note", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class RequirementLineInputSerializer(serializers.Serializer):
    """Một dòng định mức trong PUT /requirements/ (bulk replace)."""

    material_id = serializers.PrimaryKeyRelatedField(
        queryset=Material.objects.all(), source="material"
    )
    quantity = serializers.DecimalField(
        max_digits=14, decimal_places=3, min_value=Decimal("0.001")
    )
    note = serializers.CharField(required=False, allow_blank=True, default="")


class RequirementsUpdateSerializer(serializers.Serializer):
    lines = RequirementLineInputSerializer(many=True, allow_empty=True)

    def validate(self, attrs):
        seen = set()
        for item in attrs["lines"]:
            material = item["material"]
            if material.id in seen:
                raise serializers.ValidationError(
                    {"lines": f"Trùng vật tư {material.code} trong danh sách định mức."}
                )
            seen.add(material.id)
        return attrs


class SettleLineInputSerializer(serializers.Serializer):
    """Một dòng trả về kho khác khi tất toán."""

    material_id = serializers.PrimaryKeyRelatedField(
        queryset=Material.objects.all(), source="material"
    )
    quantity = serializers.DecimalField(
        max_digits=14, decimal_places=3, min_value=Decimal("0.001")
    )
    note = serializers.CharField(required=False, allow_blank=True, default="")


class SettleSerializer(serializers.Serializer):
    """Body POST /sites/{id}/settle/ — cấu trúc; nghiệp vụ validate ở service."""

    to_warehouse_id = serializers.PrimaryKeyRelatedField(
        queryset=Warehouse.objects.all(), source="to_warehouse"
    )
    lines = SettleLineInputSerializer(many=True, allow_empty=False)

    def validate(self, attrs):
        seen = set()
        for item in attrs["lines"]:
            material = item["material"]
            if material.id in seen:
                raise serializers.ValidationError(
                    {"lines": f"Trùng vật tư {material.code} trong danh sách trả về."}
                )
            seen.add(material.id)
        return attrs