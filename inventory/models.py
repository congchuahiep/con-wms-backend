from django.conf import settings
from django.db import models, transaction
from django.db.models import Q, Sum
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from catalog.models import Material
from supplier.models import Supplier
from warehouse.models import Warehouse


class BaseNote(models.Model):
    """Khung chung của mọi chứng từ kho — abstract, không tạo bảng.

    Gom phần giống 100% giữa các loại phiếu (InboundNote, OutboundNote,
    StocktakeNote...): field khung, index và vòng đời nháp → chốt → hủy.
    Mỗi loại phiếu con chỉ cần viết 2 hook sinh dòng sổ kho riêng của nó.
    """

    class Status(models.TextChoices):
        DRAFT = "draft", "Nháp"
        POSTED = "posted", "Đã chốt"
        VOIDED = "voided", "Đã hủy"

    id = models.BigAutoField(primary_key=True)
    number = models.CharField(max_length=30, unique=True, verbose_name="Số phiếu")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name="Trạng thái",
    )
    date = models.DateField(default=timezone.localdate, verbose_name="Ngày nghiệp vụ")
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name="%(class)s_notes",
        verbose_name="Kho",
    )
    note = models.TextField(blank=True, verbose_name="Ghi chú")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="%(class)s_created",
        verbose_name="Người lập",
    )
    voided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="%(class)s_voided",
        verbose_name="Người hủy",
    )
    voided_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Thời điểm hủy"
    )
    void_reason = models.TextField(blank=True, verbose_name="Lý do hủy")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ngày cập nhật")

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["date"], name="ix_%(class)s_date"),
            models.Index(fields=["status"], name="ix_%(class)s_status"),
            models.Index(fields=["warehouse"], name="ix_%(class)s_warehouse"),
        ]

    @property
    def is_draft(self):
        return self.status == self.Status.DRAFT

    @property
    def is_posted(self):
        return self.status == self.Status.POSTED

    @property
    def is_voided(self):
        return self.status == self.Status.VOIDED

    def _assert_warehouse_open(self):
        """Chặn giao dịch trên kho đã đóng (kho công trường đã tất toán/ngừng hoạt động)."""
        if not self.warehouse.is_active:
            raise ValidationError(
                {"warehouse": "Kho đã đóng — không thực hiện giao dịch."}
            )
        site = getattr(self.warehouse, "site", None)
        if site is not None and site.status != site.Status.ACTIVE:  # ty: ignore[unresolved-attribute]
            raise ValidationError(
                {"warehouse": "Kho công trường đã đóng — không thực hiện giao dịch."}
            )

    @transaction.atomic
    def post(self, user):
        """Chốt phiếu: sinh dòng sổ kho theo hook của loại phiếu, chuyển posted."""
        if not self.is_draft:
            raise ValidationError({"status": "Chỉ phiếu nháp mới được chốt."})
        self._assert_warehouse_open()
        for movement in self._build_post_movements(user):
            movement.save()
        self.status = self.Status.POSTED
        self.save(update_fields=["status", "updated_at"])

    @transaction.atomic
    def void(self, reason, user):
        """Hủy phiếu đã chốt: ghi dòng ngược dấu, lưu ai hủy/khi nào/lý do."""
        if not self.is_posted:
            raise ValidationError({"status": "Chỉ phiếu đã chốt mới được hủy."})
        self._assert_warehouse_open()
        for movement in self._build_void_movements(reason, user):
            movement.save()
        self.status = self.Status.VOIDED
        self.voided_by = user
        self.voided_at = timezone.now()
        self.void_reason = reason
        self.save(
            update_fields=[
                "status",
                "voided_by",
                "voided_at",
                "void_reason",
                "updated_at",
            ]
        )

    def _build_post_movements(self, user):
        raise NotImplementedError

    def _build_void_movements(self, reason, user):
        raise NotImplementedError


class InboundNote(BaseNote):
    class Type(models.TextChoices):
        PURCHASE = "purchase", "Mua hàng từ nhà cung cấp"
        RETURN_FROM_SITE = "return_from_site", "Công trường trả lại hàng"

    note_type = models.CharField(
        max_length=20,
        choices=Type.choices,
        default=Type.PURCHASE,
        verbose_name="Loại phiếu",
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="inbound_notes",
        verbose_name="Nhà cung cấp",
    )
    site = models.ForeignKey(
        "sites.Site",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="inbound_notes",
        verbose_name="Công trường",
    )

    class Meta(BaseNote.Meta):
        db_table = "inbound_note"
        verbose_name = "Phiếu nhập"
        verbose_name_plural = "Phiếu nhập"
        indexes = [
            *(index.clone() for index in BaseNote.Meta.indexes),
            models.Index(fields=["supplier"], name="ix_inbound_note_supplier"),
            models.Index(fields=["site"], name="ix_inbound_note_site"),
        ]

    def __str__(self):
        return f"{self.number} - {self.get_note_type_display()}"  # ty: ignore[unresolved-attribute]

    def _build_post_movements(self, user):
        movement_type = (
            StockMovement.Type.INBOUND_PURCHASE_FROM_SUPPLIER
            if self.note_type == self.Type.PURCHASE
            else StockMovement.Type.INBOUND_RETURN_FROM_SITE
        )
        movements = []
        for line in self.lines.select_related("material"):  # ty: ignore[unresolved-attribute]
            movements.append(
                StockMovement(
                    material=line.material,
                    warehouse=self.warehouse,
                    quantity=line.quantity,
                    unit_price=(
                        line.unit_price
                        if self.note_type == self.Type.PURCHASE
                        else None
                    ),
                    movement_type=movement_type,
                    date=self.date,
                    inbound_note=self,
                    created_by=user,
                )
            )
        return movements

    def _build_void_movements(self, reason, user):
        movements = []
        for movement in self.stock_movements.filter(  # ty: ignore[unresolved-attribute]
            reversal_of__isnull=True
        ):
            movements.append(
                StockMovement(
                    material=movement.material,
                    warehouse=movement.warehouse,
                    quantity=-movement.quantity,
                    unit_price=movement.unit_price,
                    movement_type=movement.movement_type,
                    date=timezone.localdate(),
                    inbound_note=self,
                    reversal_of=movement,
                    reason=reason,
                    created_by=user,
                )
            )
        return movements


class InboundNoteLine(models.Model):
    id = models.BigAutoField(primary_key=True)
    inbound_note = models.ForeignKey(
        InboundNote,
        on_delete=models.CASCADE,
        related_name="lines",
        verbose_name="Phiếu nhập",
    )
    material = models.ForeignKey(
        Material,
        on_delete=models.PROTECT,
        related_name="inbound_lines",
        verbose_name="Vật tư",
    )
    quantity = models.DecimalField(
        max_digits=14, decimal_places=3, verbose_name="Số lượng"
    )
    unit_price = models.DecimalField(
        max_digits=14, decimal_places=2, verbose_name="Đơn giá"
    )
    line_no = models.IntegerField(default=0, verbose_name="Thứ tự dòng")
    note = models.TextField(blank=True, verbose_name="Ghi chú")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ngày cập nhật")

    class Meta:
        db_table = "inbound_note_line"
        verbose_name = "Dòng phiếu nhập"
        verbose_name_plural = "Dòng phiếu nhập"
        ordering = ["line_no", "id"]

    def __str__(self):
        return f"{self.material.code} x {self.quantity}"


class StockMovement(models.Model):
    """Dòng sổ kho - bất biến, chỉ sinh ra qua chốt/hủy phiếu."""

    class Type(models.TextChoices):
        """Loại dòng sổ kho.

        Quy ước đặt tên: giá trị bắt đầu bằng hướng tồn kho — `inbound_`
        (hàng vào kho, quantity dương), `outbound_` (hàng ra khỏi kho,
        quantity âm), `stocktake_` (điều chỉnh tồn, dấu tùy chênh lệch).
        Phần còn lại nói rõ lý do và đối tượng liên quan của biến động.
        """

        INBOUND_PURCHASE_FROM_SUPPLIER = (
            "inbound_purchase_from_supplier",
            "Nhập kho: mua hàng từ nhà cung cấp",
        )
        INBOUND_RETURN_FROM_SITE = (
            "inbound_return_from_site",
            "Nhập kho: công trường trả lại hàng",
        )
        OUTBOUND_ISSUE_FOR_USE = (
            "outbound_issue_for_use",
            "Xuất kho: cấp phát để sử dụng",
        )
        OUTBOUND_TRANSFER_TO_WAREHOUSE = (
            "outbound_transfer_to_warehouse",
            "Xuất kho: điều chuyển sang kho khác",
        )
        INBOUND_TRANSFER_FROM_WAREHOUSE = (
            "inbound_transfer_from_warehouse",
            "Nhập kho: điều chuyển từ kho khác",
        )
        STOCKTAKE_ADJUSTMENT = (
            "stocktake_adjustment",
            "Điều chỉnh tồn: chênh lệch kiểm kê",
        )

    id = models.BigAutoField(primary_key=True)
    material = models.ForeignKey(
        Material,
        on_delete=models.PROTECT,
        related_name="stock_movements",
        verbose_name="Vật tư",
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name="stock_movements",
        verbose_name="Kho",
    )
    quantity = models.DecimalField(
        max_digits=14, decimal_places=3, verbose_name="Số lượng (+/−)"
    )
    unit_price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Đơn giá",
    )
    movement_type = models.CharField(
        max_length=40,
        choices=Type.choices,
        verbose_name="Loại biến động",
    )
    date = models.DateField(verbose_name="Ngày nghiệp vụ")
    inbound_note = models.ForeignKey(
        InboundNote,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="stock_movements",
        verbose_name="Phiếu nhập nguồn",
    )
    outbound_note = models.ForeignKey(
        "OutboundNote",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="stock_movements",
        verbose_name="Phiếu xuất nguồn",
    )
    stocktake_note = models.ForeignKey(
        "StocktakeNote",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="stock_movements",
        verbose_name="Phiếu kiểm kê nguồn",
    )
    lot = models.CharField(max_length=50, null=True, blank=True, verbose_name="Lô")
    reversal_of = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="reversals",
        verbose_name="Đảo ngược của dòng",
    )
    reason = models.TextField(blank=True, verbose_name="Lý do")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="stock_movements_created",
        verbose_name="Người ghi sổ",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày ghi sổ")

    class Meta:
        db_table = "stock_movement"
        verbose_name = "Dòng sổ kho"
        verbose_name_plural = "Dòng sổ kho"
        indexes = [
            models.Index(
                fields=["warehouse", "material", "date"],
                name="ix_sm_warehouse_material_date",
            ),
            models.Index(fields=["movement_type", "date"], name="ix_sm_type_date"),
            models.Index(fields=["inbound_note"], name="ix_sm_inbound_note"),
            models.Index(fields=["outbound_note"], name="ix_sm_outbound_note"),
            models.Index(fields=["stocktake_note"], name="ix_sm_stocktake_note"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(
                        inbound_note__isnull=False,
                        outbound_note__isnull=True,
                        stocktake_note__isnull=True,
                    )
                    | Q(
                        inbound_note__isnull=True,
                        outbound_note__isnull=False,
                        stocktake_note__isnull=True,
                    )
                    | Q(
                        inbound_note__isnull=True,
                        outbound_note__isnull=True,
                        stocktake_note__isnull=False,
                    )
                ),
                name="ck_sm_exactly_one_source",
            ),
            models.CheckConstraint(
                condition=(
                    Q(
                        unit_price__isnull=False,
                        movement_type="inbound_purchase_from_supplier",
                    )
                    | Q(unit_price__isnull=True)
                    & ~Q(movement_type="inbound_purchase_from_supplier")
                ),
                name="ck_sm_price_only_purchase",
            ),
        ]

    def __str__(self):
        return (
            f"{self.get_movement_type_display()} "  # ty: ignore[unresolved-attribute]
            f"{self.material.code} {self.quantity:+.3f} @ {self.warehouse.code}"
        )


class OutboundNote(BaseNote):
    class Type(models.TextChoices):
        ISSUE_FOR_USE = "issue_for_use", "Xuất cấp cho công trường sử dụng"
        TRANSFER = "transfer", "Điều chuyển kho"

    note_type = models.CharField(
        max_length=20,
        choices=Type.choices,
        default=Type.ISSUE_FOR_USE,
        verbose_name="Loại phiếu",
    )
    to_warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="outbound_to_notes",
        verbose_name="Kho đích",
    )
    site = models.ForeignKey(
        "sites.Site",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="outbound_notes",
        verbose_name="Công trường",
    )

    class Meta(BaseNote.Meta):
        db_table = "outbound_note"
        verbose_name = "Phiếu xuất"
        verbose_name_plural = "Phiếu xuất"
        indexes = [
            *(index.clone() for index in BaseNote.Meta.indexes),
            models.Index(fields=["to_warehouse"], name="ix_outbound_note_to_warehouse"),
            models.Index(fields=["site"], name="ix_outbound_note_site"),
        ]

    def __str__(self):
        return f"{self.number} - {self.get_note_type_display()}"  # ty: ignore[unresolved-attribute]

    def _build_post_movements(self, user):
        movements = []
        for line in self.lines.select_related("material"):  # ty: ignore[unresolved-attribute]
            stock = (
                StockMovement.objects.filter(
                    warehouse=self.warehouse, material=line.material
                ).aggregate(s=Sum("quantity"))["s"]
                or 0
            )
            if stock < line.quantity:
                raise ValidationError(
                    {
                        "lines": f"Không đủ tồn {line.material.code}: tồn {stock}, cần {line.quantity}."
                    }
                )
            if self.note_type == self.Type.ISSUE_FOR_USE:
                movements.append(
                    StockMovement(
                        material=line.material,
                        warehouse=self.warehouse,
                        quantity=-line.quantity,
                        movement_type=StockMovement.Type.OUTBOUND_ISSUE_FOR_USE,
                        date=self.date,
                        outbound_note=self,
                        created_by=user,
                    )
                )
            else:
                movements.append(
                    StockMovement(
                        material=line.material,
                        warehouse=self.warehouse,
                        quantity=-line.quantity,
                        movement_type=StockMovement.Type.OUTBOUND_TRANSFER_TO_WAREHOUSE,
                        date=self.date,
                        outbound_note=self,
                        created_by=user,
                    )
                )
                movements.append(
                    StockMovement(
                        material=line.material,
                        warehouse=self.to_warehouse,
                        quantity=line.quantity,
                        movement_type=StockMovement.Type.INBOUND_TRANSFER_FROM_WAREHOUSE,
                        date=self.date,
                        outbound_note=self,
                        created_by=user,
                    )
                )
        return movements

    def _build_void_movements(self, reason, user):
        movements = []
        for m in self.stock_movements.filter(reversal_of__isnull=True):  # ty: ignore[unresolved-attribute]
            movements.append(
                StockMovement(
                    material=m.material,
                    warehouse=m.warehouse,
                    quantity=-m.quantity,
                    movement_type=m.movement_type,
                    date=timezone.localdate(),
                    outbound_note=self,
                    reversal_of=m,
                    reason=reason,
                    created_by=user,
                )
            )
        return movements


class OutboundNoteLine(models.Model):
    id = models.BigAutoField(primary_key=True)
    outbound_note = models.ForeignKey(
        OutboundNote,
        on_delete=models.CASCADE,
        related_name="lines",
        verbose_name="Phiếu xuất",
    )
    material = models.ForeignKey(
        Material,
        on_delete=models.PROTECT,
        related_name="outbound_lines",
        verbose_name="Vật tư",
    )
    quantity = models.DecimalField(
        max_digits=14, decimal_places=3, verbose_name="Số lượng"
    )
    line_no = models.IntegerField(default=0, verbose_name="Thứ tự dòng")
    note = models.TextField(blank=True, verbose_name="Ghi chú")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ngày cập nhật")

    class Meta:
        db_table = "outbound_note_line"
        verbose_name = "Dòng phiếu xuất"
        verbose_name_plural = "Dòng phiếu xuất"
        ordering = ["line_no", "id"]


class StocktakeNote(BaseNote):
    class Meta(BaseNote.Meta):
        db_table = "stocktake_note"
        verbose_name = "Phiếu kiểm kê"
        verbose_name_plural = "Phiếu kiểm kê"

    def __str__(self):
        return f"{self.number}"

    def _build_post_movements(self, user):
        movements = []
        for line in self.lines.select_related("material"):  # ty: ignore[unresolved-attribute]
            if not line.reason:
                raise ValidationError(
                    {"lines": f"Dòng {line.material.code} thiếu lý do."}
                )
            if line.difference == 0:
                raise ValidationError(
                    {"lines": f"Dòng {line.material.code} chênh lệch phải khác 0."}
                )
            stock = (
                StockMovement.objects.filter(
                    warehouse=self.warehouse, material=line.material
                ).aggregate(s=Sum("quantity"))["s"]
                or 0
            )
            if line.difference < -stock:
                raise ValidationError(
                    {
                        "lines": f"Dòng {line.material.code} chênh lệch {line.difference} làm tồn âm (tồn {stock})."
                    }
                )
            movements.append(
                StockMovement(
                    material=line.material,
                    warehouse=self.warehouse,
                    quantity=line.difference,
                    movement_type=StockMovement.Type.STOCKTAKE_ADJUSTMENT,
                    date=self.date,
                    stocktake_note=self,
                    reason=line.reason,
                    created_by=user,
                )
            )
        return movements

    def _build_void_movements(self, reason, user):
        movements = []
        for m in self.stock_movements.filter(reversal_of__isnull=True):  # ty: ignore[unresolved-attribute]
            movements.append(
                StockMovement(
                    material=m.material,
                    warehouse=m.warehouse,
                    quantity=-m.quantity,
                    movement_type=m.movement_type,
                    date=timezone.localdate(),
                    stocktake_note=self,
                    reversal_of=m,
                    reason=reason,
                    created_by=user,
                )
            )
        return movements


class StocktakeLine(models.Model):
    id = models.BigAutoField(primary_key=True)
    stocktake_note = models.ForeignKey(
        StocktakeNote,
        on_delete=models.CASCADE,
        related_name="lines",
        verbose_name="Phiếu kiểm kê",
    )
    material = models.ForeignKey(
        Material,
        on_delete=models.PROTECT,
        related_name="stocktake_lines",
        verbose_name="Vật tư",
    )
    difference = models.DecimalField(
        max_digits=14, decimal_places=3, verbose_name="Chênh lệch"
    )
    reason = models.TextField(blank=True, verbose_name="Lý do")
    line_no = models.IntegerField(default=0, verbose_name="Thứ tự dòng")
    note = models.TextField(blank=True, verbose_name="Ghi chú")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ngày cập nhật")

    class Meta:
        db_table = "stocktake_line"
        verbose_name = "Dòng kiểm kê"
        verbose_name_plural = "Dòng kiểm kê"
        ordering = ["line_no", "id"]
