from collections import OrderedDict
from decimal import Decimal

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import Material, MaterialCategory, Unit, UnitConversion


class SimpleCategorySerializer(serializers.ModelSerializer):
    """Dùng để nhúng vào MaterialSerializer output."""

    class Meta:
        model = MaterialCategory
        fields = ["id", "code", "name", "color"]


class SimpleUnitSerializer(serializers.ModelSerializer):
    """Dùng để nhúng vào MaterialSerializer / UnitConversionSerializer output."""

    class Meta:
        model = Unit
        fields = ["id", "code", "name"]


class SimpleMaterialSerializer(serializers.ModelSerializer):
    """Dùng để nhúng vào UnitConversionSerializer output."""

    class Meta:
        model = Material
        fields = ["id", "code", "name"]


class MaterialCategorySerializer(serializers.ModelSerializer):
    """
    Serializer chính cho MaterialCategory CRUD.
    Khi list gốc (parent=null) trả về dạng cây lồng đệ quy.
    Khi create/update: input parent_id (write_only), output parent {id, code, name, color}.
    """

    parent_id = serializers.PrimaryKeyRelatedField(
        queryset=MaterialCategory.objects.all(),
        source="parent",
        required=False,
        allow_null=True,
    )
    children = serializers.SerializerMethodField()

    class Meta:
        model = MaterialCategory
        fields = [
            "id",
            "code",
            "name",
            "color",
            "parent_id",
            "children",
            "description",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    @extend_schema_field(serializers.ListField(child=serializers.DictField()))
    def get_children(self, obj):
        children = obj.children.filter(is_active=True)
        if not children.exists():
            return []
        return MaterialCategorySerializer(children, many=True).data

    def to_representation(self, instance):
        """Trả về parent dạng object {id, code, name, color} thay vì chỉ id."""
        data = super().to_representation(instance)
        if instance.parent:
            data["parent"] = SimpleCategorySerializer(instance.parent).data
        return data


class MaterialCategoryFlatSerializer(serializers.ModelSerializer):
    """
    Dạng phẳng, dùng cho select box. GET /api/categories/?flat=true.
    Duyệt pre-order, mỗi item có field `depth`.
    """

    depth = serializers.SerializerMethodField()

    class Meta:
        model = MaterialCategory
        fields = [
            "id",
            "code",
            "name",
            "color",
            "parent",
            "depth",
            "is_active",
        ]

    def get_depth(self, obj):
        depth = 0
        current = obj.parent
        while current is not None:
            depth += 1
            current = current.parent
        return depth

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.parent:
            data["parent"] = instance.parent_id
        return data


class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = [
            "id",
            "code",
            "name",
            "conversion_type",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class UnitConversionSerializer(serializers.ModelSerializer):
    from_unit_id = serializers.PrimaryKeyRelatedField(
        queryset=Unit.objects.filter(is_active=True),
        source="from_unit",
        write_only=True,
        required=False,
    )
    to_unit_id = serializers.PrimaryKeyRelatedField(
        queryset=Unit.objects.filter(is_active=True),
        source="to_unit",
        write_only=True,
    )
    material_id = serializers.PrimaryKeyRelatedField(
        queryset=Material.objects.filter(is_active=True),
        source="material",
        write_only=True,
        required=False,
        allow_null=True,
        default=None,
    )

    from_unit = SimpleUnitSerializer(read_only=True)
    to_unit = SimpleUnitSerializer(read_only=True)
    material = SimpleMaterialSerializer(read_only=True, allow_null=True)
    is_reverse = serializers.BooleanField(read_only=True, default=False)

    class Meta:
        model = UnitConversion
        fields = [
            "id",
            "from_unit_id",
            "to_unit_id",
            "material_id",
            "from_unit",
            "to_unit",
            "factor",
            "material",
            "is_reverse",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "from_unit",
            "to_unit",
            "material",
            "is_reverse",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        from_unit = attrs.get("from_unit")
        to_unit = attrs.get("to_unit")
        material = attrs.get("material")

        if not from_unit and self.instance:
            from_unit = self.instance.from_unit
        if not to_unit and self.instance:
            to_unit = self.instance.to_unit
        if "material" not in attrs and self.instance:
            material = self.instance.material

        if from_unit:
            if from_unit.conversion_type == "global" and material is not None:
                raise serializers.ValidationError(
                    {"material_id": "Đơn vị toàn cục không được gán vật tư."}
                )
            if from_unit.conversion_type == "material" and material is None:
                raise serializers.ValidationError(
                    {"material_id": "Đơn vị theo vật tư bắt buộc phải chọn vật tư."}
                )

        # Ngăn tạo reverse pair cho global (API đã có reverse virtual)
        if (
            from_unit
            and to_unit
            and from_unit.conversion_type == "global"
            and not self.instance
        ):
            exists = UnitConversion.objects.filter(
                from_unit=to_unit,
                to_unit=from_unit,
                material__isnull=True,
            ).exists()
            if exists:
                raise serializers.ValidationError(
                    {
                        "to_unit_id": (
                            f"Đã tồn tại quy đổi ({to_unit.code} <-> {from_unit.code})."
                        )
                    }
                )

        # Kiểm tra trùng lặp (thay cho IntegrityError 500 từ DB)
        if from_unit and to_unit:
            qs = UnitConversion.objects.filter(
                from_unit=from_unit,
                to_unit=to_unit,
                material__isnull=(material is None),
            )
            if material is not None:
                qs = qs.filter(material=material)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                if material is None:
                    raise serializers.ValidationError(
                        {
                            "to_unit_id": f"Đã tồn tại quy đổi ({from_unit.code} <-> {to_unit.code})."
                        }
                    )
                else:
                    raise serializers.ValidationError(
                        {
                            "to_unit_id": f"Đã tồn tại quy đổi ({from_unit.code} <-> {to_unit.code})."
                        }
                    )

        return attrs

    @staticmethod
    def _format_factor(value):
        """Strip trailing zeros: '500.0000' -> '500', '0.0010' -> '0.001'."""
        s = str(Decimal(str(value)))
        if "." in s:
            s = s.rstrip("0").rstrip(".")
        return s

    def to_representation(self, instance):
        if self.context.get("reverse"):
            return OrderedDict(
                [
                    ("id", instance.id),
                    (
                        "from_unit",
                        SimpleUnitSerializer(
                            instance.to_unit, context=self.context
                        ).data,
                    ),
                    (
                        "to_unit",
                        SimpleUnitSerializer(
                            instance.from_unit, context=self.context
                        ).data,
                    ),
                    ("factor", self._format_factor(Decimal(1) / instance.factor)),
                    (
                        "material",
                        (
                            SimpleMaterialSerializer(
                                instance.material, context=self.context
                            ).data
                            if instance.material
                            else None
                        ),
                    ),
                    ("is_reverse", True),
                    ("is_active", instance.is_active),
                    (
                        "created_at",
                        instance.created_at.isoformat()
                        if instance.created_at
                        else None,
                    ),
                    (
                        "updated_at",
                        instance.updated_at.isoformat()
                        if instance.updated_at
                        else None,
                    ),
                ]
            )
        data = super().to_representation(instance)
        data["factor"] = self._format_factor(data["factor"])
        return data


class DetailedUnitSerializer(serializers.ModelSerializer):
    """Dùng cho GET /api/units/{id}/conversions/ — chi tiết unit kèm danh sách quy đổi."""

    conversions = serializers.SerializerMethodField()

    class Meta:
        model = Unit
        fields = [
            "id",
            "code",
            "name",
            "conversion_type",
            "is_active",
            "created_at",
            "updated_at",
            "conversions",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    @extend_schema_field(UnitConversionSerializer(many=True))
    def get_conversions(self, obj):
        result = []

        # 1. Direct conversions
        direct = obj.conversions_from.filter(is_active=True).select_related(
            "to_unit", "material"
        )
        result.extend(
            UnitConversionSerializer(direct, many=True, context=self.context).data
        )

        # 2. Reverse conversions — only for global units
        if obj.conversion_type == "global":
            reverse = UnitConversion.objects.filter(
                to_unit=obj, is_active=True, material__isnull=True
            ).select_related("from_unit")

            ctx = {**self.context, "reverse": True}
            result.extend(
                UnitConversionSerializer(reverse, many=True, context=ctx).data
            )

        return result


class MaterialSerializer(serializers.ModelSerializer):
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=MaterialCategory.objects.filter(is_active=True),
        source="category",
        write_only=True,
    )
    unit_id = serializers.PrimaryKeyRelatedField(
        queryset=Unit.objects.filter(is_active=True),
        source="unit",
        write_only=True,
    )
    category = SimpleCategorySerializer(read_only=True)
    unit = SimpleUnitSerializer(read_only=True)

    class Meta:
        model = Material
        fields = [
            "id",
            "code",
            "name",
            "category_id",
            "category",
            "unit_id",
            "unit",
            "description",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
