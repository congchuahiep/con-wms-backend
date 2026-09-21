from decimal import Decimal

from django.db import transaction
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from catalog.models import Material
from catalog.serializers import (
    SimpleCategorySerializer,
    SimpleMaterialSerializer,
    SimpleUnitSerializer,
)
from iam.models import User
from sites.models import Site
from supplier.models import Supplier
from warehouse.models import Warehouse

from .models import (
    InboundNote,
    InboundNoteLine,
    OutboundNote,
    OutboundNoteLine,
    StockMovement,
    StocktakeLine,
    StocktakeNote,
)


class SimpleWarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = ["id", "code", "name"]


def _ensure_warehouse_open(warehouse):
    """Chặn tạo/sửa phiếu trên kho đã đóng (kho công trường đã tất toán/ngừng)."""
    if not warehouse.is_active:
        raise serializers.ValidationError(
            {"warehouse": "Kho đã đóng — không lập/sửa phiếu được."}
        )
    site = getattr(warehouse, "site", None)
    if site is not None and site.status != site.Status.ACTIVE:  # ty: ignore[unresolved-attribute]
        raise serializers.ValidationError(
            {"warehouse": "Kho công trường đã đóng — không lập/sửa phiếu được."}
        )


class SimpleSupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ["id", "code", "name"]


class SimpleSiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Site
        fields = ["id", "code", "name"]


class SimpleUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email"]


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
    site_id = serializers.PrimaryKeyRelatedField(
        queryset=Site.objects.all(),
        source="site",
        write_only=True,
        required=False,
        allow_null=True,
    )
    warehouse = SimpleWarehouseSerializer(read_only=True)
    supplier = SimpleSupplierSerializer(read_only=True)
    site = SimpleSiteSerializer(read_only=True)
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
            "site_id",
            "site",
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
        site = attrs.get("site")
        if "site" not in attrs and self.instance:
            site = self.instance.site

        warehouse = attrs.get("warehouse", getattr(self.instance, "warehouse", None))
        if warehouse is not None:
            _ensure_warehouse_open(warehouse)

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
        if note_type == InboundNote.Type.RETURN_FROM_SITE and site is None:
            raise serializers.ValidationError(
                {"site_id": "Phiếu trả lại hàng phải chọn công trường."}
            )
        if note_type == InboundNote.Type.PURCHASE and site is not None:
            raise serializers.ValidationError(
                {"site_id": "Phiếu nhập mua không được chọn công trường."}
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


class OutboundNoteLineSerializer(serializers.ModelSerializer):
    material_id = serializers.PrimaryKeyRelatedField(
        queryset=Material.objects.all(), source="material", write_only=True
    )
    material = SimpleMaterialSerializer(read_only=True)

    class Meta:
        model = OutboundNoteLine
        fields = ["id", "material_id", "material", "quantity", "line_no", "note"]
        read_only_fields = ["id", "line_no"]

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Số lượng phải lớn hơn 0.")
        return value


class OutboundNoteSerializer(serializers.ModelSerializer):
    warehouse_id = serializers.PrimaryKeyRelatedField(
        queryset=Warehouse.objects.all(), source="warehouse", write_only=True
    )
    site_id = serializers.PrimaryKeyRelatedField(
        queryset=Site.objects.all(),
        source="site",
        write_only=True,
        required=False,
        allow_null=True,
    )
    to_warehouse_id = serializers.PrimaryKeyRelatedField(
        queryset=Warehouse.objects.all(),
        source="to_warehouse",
        write_only=True,
        required=False,
        allow_null=True,
    )
    warehouse = SimpleWarehouseSerializer(read_only=True)
    site = SimpleSiteSerializer(read_only=True)
    to_warehouse = SimpleWarehouseSerializer(read_only=True)
    created_by = SimpleUserSerializer(read_only=True)
    voided_by = SimpleUserSerializer(read_only=True)
    lines = OutboundNoteLineSerializer(many=True)
    note_type_label = serializers.CharField(
        source="get_note_type_display", read_only=True
    )
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    total_quantity = serializers.SerializerMethodField()

    class Meta:
        model = OutboundNote
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
            "site_id",
            "site",
            "to_warehouse_id",
            "to_warehouse",
            "created_by",
            "voided_by",
            "voided_at",
            "void_reason",
            "note",
            "lines",
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

    @extend_schema_field(serializers.IntegerField())
    def get_total_quantity(self, obj):
        return len(obj.lines.all())

    def validate(self, attrs):
        note_type = attrs.get("note_type", getattr(self.instance, "note_type", None))
        site = attrs.get("site")
        if "site" not in attrs and self.instance:
            site = self.instance.site
        to_warehouse = attrs.get("to_warehouse")
        if "to_warehouse" not in attrs and self.instance:
            to_warehouse = self.instance.to_warehouse

        warehouse = attrs.get("warehouse", getattr(self.instance, "warehouse", None))
        if warehouse is not None:
            _ensure_warehouse_open(warehouse)
        if to_warehouse is not None:
            _ensure_warehouse_open(to_warehouse)

        if note_type == OutboundNote.Type.ISSUE_FOR_USE and site is None:
            raise serializers.ValidationError(
                {"site_id": "Phiếu xuất cấp phải chọn công trường."}
            )
        if note_type == OutboundNote.Type.ISSUE_FOR_USE and to_warehouse is not None:
            raise serializers.ValidationError(
                {"to_warehouse_id": "Phiếu xuất cấp không được chọn kho đích."}
            )
        if note_type == OutboundNote.Type.TRANSFER and to_warehouse is None:
            raise serializers.ValidationError(
                {"to_warehouse_id": "Phiếu điều chuyển phải chọn kho đích."}
            )
        if note_type == OutboundNote.Type.TRANSFER and site is not None:
            raise serializers.ValidationError(
                {"site_id": "Phiếu điều chuyển không được chọn công trường."}
            )
        # to_warehouse != warehouse
        wh = attrs.get("warehouse", getattr(self.instance, "warehouse", None))
        if to_warehouse and wh and to_warehouse == wh:
            raise serializers.ValidationError(
                {"to_warehouse_id": "Kho đích phải khác kho nguồn."}
            )
        # D6 — kho công trường chỉ xuất dùng cho chính công trường của nó
        if (
            wh is not None
            and getattr(wh, "site", None) is not None
            and note_type == OutboundNote.Type.ISSUE_FOR_USE
            and site != wh.site
        ):
            raise serializers.ValidationError(
                {
                    "site_id": "Kho công trường chỉ xuất dùng cho chính công trường của nó."
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
        note = OutboundNote.objects.create(**validated_data)
        self._create_lines(note, lines_data)
        return note

    @transaction.atomic
    def update(self, instance, validated_data):
        lines_data = validated_data.pop("lines", None)
        instance = super().update(instance, validated_data)
        if lines_data is not None:
            instance.lines.all().delete()
            self._create_lines(instance, lines_data)
        return instance

    def _create_lines(self, note, lines_data):
        for idx, item in enumerate(lines_data, start=1):
            OutboundNoteLine.objects.create(outbound_note=note, line_no=idx, **item)


class OutboundNoteListSerializer(OutboundNoteSerializer):
    class Meta(OutboundNoteSerializer.Meta):
        fields = tuple(f for f in OutboundNoteSerializer.Meta.fields if f != "lines")


class VoidOutboundNoteSerializer(serializers.Serializer):
    reason = serializers.CharField(required=True, allow_blank=False)


class StocktakeLineSerializer(serializers.ModelSerializer):
    material_id = serializers.PrimaryKeyRelatedField(
        queryset=Material.objects.all(), source="material", write_only=True
    )
    material = SimpleMaterialSerializer(read_only=True)

    class Meta:
        model = StocktakeLine
        fields = [
            "id",
            "material_id",
            "material",
            "difference",
            "reason",
            "line_no",
            "note",
        ]
        read_only_fields = ["id", "line_no"]

    def validate_difference(self, value):
        if value == 0:
            raise serializers.ValidationError("Chênh lệch phải khác 0.")
        return value

    def validate(self, attrs):
        reason = attrs.get(
            "reason", getattr(self.instance, "reason", "") if self.instance else ""
        )
        if not reason:
            raise serializers.ValidationError({"reason": "Phải ghi lý do chênh lệch."})
        return attrs


class StocktakeNoteSerializer(serializers.ModelSerializer):
    warehouse_id = serializers.PrimaryKeyRelatedField(
        queryset=Warehouse.objects.all(), source="warehouse", write_only=True
    )
    warehouse = SimpleWarehouseSerializer(read_only=True)
    created_by = SimpleUserSerializer(read_only=True)
    voided_by = SimpleUserSerializer(read_only=True)
    lines = StocktakeLineSerializer(many=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = StocktakeNote
        fields = [
            "id",
            "number",
            "status",
            "status_label",
            "date",
            "warehouse_id",
            "warehouse",
            "created_by",
            "voided_by",
            "voided_at",
            "void_reason",
            "note",
            "lines",
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

    def validate(self, attrs):
        warehouse = attrs.get("warehouse", getattr(self.instance, "warehouse", None))
        if warehouse is not None:
            _ensure_warehouse_open(warehouse)

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
        note = StocktakeNote.objects.create(**validated_data)
        self._create_lines(note, lines_data)
        return note

    @transaction.atomic
    def update(self, instance, validated_data):
        lines_data = validated_data.pop("lines", None)
        instance = super().update(instance, validated_data)
        if lines_data is not None:
            instance.lines.all().delete()
            self._create_lines(instance, lines_data)
        return instance

    def _create_lines(self, note, lines_data):
        for idx, item in enumerate(lines_data, start=1):
            StocktakeLine.objects.create(stocktake_note=note, line_no=idx, **item)


class StocktakeNoteListSerializer(StocktakeNoteSerializer):
    class Meta(StocktakeNoteSerializer.Meta):
        fields = tuple(f for f in StocktakeNoteSerializer.Meta.fields if f != "lines")


class VoidStocktakeNoteSerializer(serializers.Serializer):
    reason = serializers.CharField(required=True, allow_blank=False)


class StockBalanceMaterialSerializer(SimpleMaterialSerializer):
    """Material trong bảng tồn kho — kèm cả category."""

    category = SimpleCategorySerializer(read_only=True)

    class Meta(SimpleMaterialSerializer.Meta):
        fields = [*SimpleMaterialSerializer.Meta.fields, "category"]


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

    @extend_schema_field(StockBalanceMaterialSerializer())
    def get_material(self, row):
        material = self.context["materials"].get(row["material_id"])
        return StockBalanceMaterialSerializer(material).data if material else None

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


class SourceNoteRefSerializer(serializers.Serializer):
    """Phiếu nguồn của dòng sổ kho — tự mô tả loại phiếu.

    Một dòng sổ kho luôn sinh từ đúng 1 phiếu (CheckConstraint
    ck_sm_exactly_one_source), kể cả dòng reversal (trỏ về phiếu đã hủy).
    `note_type` giúp frontend render cột "Phiếu" không cần map
    `movement_type` → field — lưu ý dòng `inbound_transfer_from_warehouse`
    trỏ về CÙNG phiếu xuất điều chuyển nên có `note_type="outbound"`.
    """

    id = serializers.IntegerField()
    number = serializers.CharField()
    note_type = serializers.ChoiceField(choices=["inbound", "outbound", "stocktake"])


class StockMovementSerializer(serializers.ModelSerializer):
    material = SimpleMaterialSerializer(read_only=True)
    warehouse = SimpleWarehouseSerializer(read_only=True)
    source_note = serializers.SerializerMethodField(read_only=True)
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
            "source_note",
            "lot",
            "reversal_of",
            "reason",
            "created_by",
            "created_at",
        ]

    @extend_schema_field(SourceNoteRefSerializer())
    def get_source_note(self, obj):
        """Phiếu nguồn của dòng — đúng 1 trong 3 FK nguồn (bất biến DB)."""
        for note_type, attr in (
            ("inbound", "inbound_note"),
            ("outbound", "outbound_note"),
            ("stocktake", "stocktake_note"),
        ):
            note = getattr(obj, attr)
            if note is not None:
                return {
                    "id": note.id,
                    "number": note.number,
                    "note_type": note_type,
                }
        return None
