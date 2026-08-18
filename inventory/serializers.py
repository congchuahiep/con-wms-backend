from decimal import Decimal

from django.db import transaction
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from catalog.models import Material
from catalog.serializers import SimpleMaterialSerializer, SimpleUnitSerializer
from iam.models import User
from supplier.models import Supplier
from warehouse.models import Warehouse

from .models import InboundNote, InboundNoteLine, StockMovement


class SimpleWarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = ["id", "code", "name"]


class SimpleSupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ["id", "code", "name"]


class SimpleUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email"]


class SimpleInboundNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = InboundNote
        fields = ["id", "number"]


class InboundNoteLineSerializer(serializers.ModelSerializer):
    material_id = serializers.PrimaryKeyRelatedField(
        queryset=Material.objects.all(),
        source="material",
        write_only=True,
    )
    material = SimpleMaterialSerializer(read_only=True)

    class Meta:
        model = InboundNoteLine
        fields = [
            "id",
            "material_id",
            "material",
            "quantity",
            "unit_price",
            "line_no",
            "note",
        ]
        read_only_fields = ["id", "line_no"]

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Số lượng phải lớn hơn 0.")
        return value

    def validate_unit_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Đơn giá không được âm.")
        return value


class InboundNoteSerializer(serializers.ModelSerializer):
    warehouse_id = serializers.PrimaryKeyRelatedField(
        queryset=Warehouse.objects.all(),
        source="warehouse",
        write_only=True,
    )
    supplier_id = serializers.PrimaryKeyRelatedField(
        queryset=Supplier.objects.all(),
        source="supplier",
        write_only=True,
        required=False,
        allow_null=True,
    )
    warehouse = SimpleWarehouseSerializer(read_only=True)
    supplier = SimpleSupplierSerializer(read_only=True)
    created_by = SimpleUserSerializer(read_only=True)
    voided_by = SimpleUserSerializer(read_only=True)
    lines = InboundNoteLineSerializer(many=True)
    note_type_label = serializers.CharField(
        source="get_note_type_display", read_only=True
    )
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    total_amount = serializers.SerializerMethodField()
    total_quantity = serializers.SerializerMethodField()

    class Meta:
        model = InboundNote
        fields = [
            "id",
            "number",
            "note_type",
            "note_type_label",
            "status",
            "status_label",
            "date",
            "warehouse_id",
            "warehouse",
            "supplier_id",
            "supplier",
            "created_by",
            "voided_by",
            "voided_at",
            "void_reason",
            "note",
            "lines",
            "total_amount",
            "total_quantity",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "number",
            "status",
            "created_by",
            "voided_by",
            "voided_at",
            "void_reason",
            "created_at",
            "updated_at",
        ]

    @extend_schema_field(serializers.DecimalField(max_digits=14, decimal_places=2))
    def get_total_amount(self, obj):
        total = sum(
            (line.quantity * line.unit_price for line in obj.lines.all()),
            Decimal(0),
        )
        return str(total.quantize(Decimal("0.01")))

    @extend_schema_field(serializers.IntegerField())
    def get_total_quantity(self, obj):
        return len(obj.lines.all())

    def validate(self, attrs):
        note_type = attrs.get("note_type", getattr(self.instance, "note_type", None))
        supplier = attrs.get("supplier")
        if "supplier" not in attrs and self.instance:
            supplier = self.instance.supplier

        if note_type == InboundNote.Type.PURCHASE and supplier is None:
            raise serializers.ValidationError(
                {"supplier_id": "Phiếu nhập mua phải chọn nhà cung cấp."}
            )
        if note_type == InboundNote.Type.RETURN_FROM_SITE and supplier is not None:
            raise serializers.ValidationError(
                {
                    "supplier_id": "Phiếu nhập hàng công trường trả lại không được có nhà cung cấp."
                }
            )

        lines = attrs.get("lines")
        if lines is not None and len(lines) == 0:
            raise serializers.ValidationError(
                {"lines": "Phiếu phải có ít nhất 1 dòng vật tư."}
            )
        if lines is None and not self.instance:
            raise serializers.ValidationError(
                {"lines": "Phiếu phải có ít nhất 1 dòng vật tư."}
            )

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        lines_data = validated_data.pop("lines")
        note = InboundNote.objects.create(**validated_data)
        self._create_lines(note, lines_data)
        return note

    @transaction.atomic
    def update(self, instance, validated_data):
        lines_data = validated_data.pop("lines", None)
        instance = super().update(instance, validated_data)
        if lines_data is not None:
            # Replace-all: xóa dòng cũ, tạo lại theo thứ tự mới
            instance.lines.all().delete()
            self._create_lines(instance, lines_data)
        return instance

    def _create_lines(self, note, lines_data):
        for idx, item in enumerate(lines_data, start=1):
            InboundNoteLine.objects.create(
                inbound_note=note,
                line_no=idx,
                **item,
            )


class InboundNoteListSerializer(InboundNoteSerializer):
    """List gọn — không kèm lines (chi tiết mới lấy lines)."""

    class Meta(InboundNoteSerializer.Meta):
        fields = tuple(
            field for field in InboundNoteSerializer.Meta.fields if field != "lines"
        )


class VoidInboundNoteSerializer(serializers.Serializer):
    reason = serializers.CharField(required=True, allow_blank=False)


class StockBalanceSerializer(serializers.Serializer):
    """Tồn kho — được tính động từ sổ kho, không lưu DB."""

    material = serializers.SerializerMethodField()
    unit = serializers.SerializerMethodField()
    warehouse = serializers.SerializerMethodField()
    quantity = serializers.DecimalField(max_digits=14, decimal_places=3)
    last_purchase_price = serializers.DecimalField(
        max_digits=14, decimal_places=2, allow_null=True
    )
    stock_value = serializers.SerializerMethodField()

    @extend_schema_field(SimpleMaterialSerializer())
    def get_material(self, row):
        material = self.context["materials"].get(row["material_id"])
        return SimpleMaterialSerializer(material).data if material else None

    @extend_schema_field(SimpleUnitSerializer())
    def get_unit(self, row):
        material = self.context["materials"].get(row["material_id"])
        if material and material.unit_id:
            return SimpleUnitSerializer(material.unit).data
        return None

    @extend_schema_field(SimpleWarehouseSerializer())
    def get_warehouse(self, row):
        warehouse = self.context["warehouses"].get(row["warehouse_id"])
        return SimpleWarehouseSerializer(warehouse).data if warehouse else None

    @extend_schema_field(
        serializers.DecimalField(max_digits=18, decimal_places=2, allow_null=True)
    )
    def get_stock_value(self, row):
        quantity = row.get("quantity")
        price = row.get("last_purchase_price")
        if quantity is None or price is None:
            return None
        return str((quantity * price).quantize(Decimal("0.01")))


class StockMovementSerializer(serializers.ModelSerializer):
    material = SimpleMaterialSerializer(read_only=True)
    warehouse = SimpleWarehouseSerializer(read_only=True)
    inbound_note = SimpleInboundNoteSerializer(read_only=True)
    created_by = SimpleUserSerializer(read_only=True)
    movement_type_label = serializers.CharField(
        source="get_movement_type_display", read_only=True
    )

    class Meta:
        model = StockMovement
        fields = [
            "id",
            "movement_type",
            "movement_type_label",
            "date",
            "material",
            "warehouse",
            "quantity",
            "unit_price",
            "inbound_note",
            "lot",
            "reversal_of",
            "reason",
            "created_by",
            "created_at",
        ]
