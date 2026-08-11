from django.db import models


class UnitConversionType(models.TextChoices):
    GLOBAL = "global", "Quy đổi toàn cục"
    MATERIAL = "material", "Quy đổi theo vật tư"


class MaterialCategory(models.Model):
    """Danh mục vật tư dạng tree (self-referential FK)."""

    id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=20, unique=True, verbose_name="Mã danh mục")
    name = models.CharField(max_length=200, verbose_name="Tên danh mục")
    color = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name="Màu sắc",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="children",
        verbose_name="Danh mục cha",
    )
    description = models.TextField(blank=True, verbose_name="Mô tả")
    is_active = models.BooleanField(default=True, verbose_name="Đang sử dụng")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ngày cập nhật")

    class Meta:
        db_table = "material_category"
        verbose_name = "Danh mục vật tư"
        verbose_name_plural = "Danh mục vật tư"
        indexes = [
            models.Index(fields=["parent"]),
        ]

    def __str__(self):
        return f"{self.code} — {self.name}"


class Unit(models.Model):
    """Đơn vị tính (BAO, KG, TAN, M3...)."""

    id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=10, unique=True, verbose_name="Mã đơn vị")
    name = models.CharField(max_length=100, verbose_name="Tên đơn vị")
    conversion_type = models.CharField(
        max_length=10,
        choices=UnitConversionType.choices,
        default=UnitConversionType.GLOBAL,
        verbose_name="Loại quy đổi",
    )
    is_active = models.BooleanField(default=True, verbose_name="Đang sử dụng")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ngày cập nhật")

    class Meta:
        db_table = "unit"
        verbose_name = "Đơn vị tính"
        verbose_name_plural = "Đơn vị tính"

    def __str__(self):
        return f"{self.code} ({self.name})"


class Material(models.Model):
    """Vật tư."""

    id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=30, unique=True, verbose_name="Mã vật tư")
    name = models.CharField(max_length=300, verbose_name="Tên vật tư")
    category = models.ForeignKey(
        MaterialCategory,
        on_delete=models.PROTECT,
        related_name="materials",
        verbose_name="Danh mục",
    )
    unit = models.ForeignKey(
        Unit,
        on_delete=models.PROTECT,
        related_name="materials",
        verbose_name="Đơn vị tính",
    )
    description = models.TextField(blank=True, verbose_name="Mô tả")
    is_active = models.BooleanField(default=True, verbose_name="Đang sử dụng")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ngày cập nhật")

    class Meta:
        db_table = "material"
        verbose_name = "Vật tư"
        verbose_name_plural = "Vật tư"
        indexes = [
            models.Index(fields=["category"]),
        ]

    def __str__(self):
        return f"{self.code} — {self.name}"


class UnitConversion(models.Model):
    """Quy đổi đơn vị: 1 from_unit = factor to_unit (có thể giới hạn theo vật tư)."""

    id = models.BigAutoField(primary_key=True)
    from_unit = models.ForeignKey(
        Unit,
        on_delete=models.PROTECT,
        related_name="conversions_from",
        verbose_name="Đơn vị gốc",
    )
    to_unit = models.ForeignKey(
        Unit,
        on_delete=models.PROTECT,
        related_name="conversions_to",
        verbose_name="Đơn vị đích",
    )
    factor = models.DecimalField(
        max_digits=12, decimal_places=4, verbose_name="Hệ số quy đổi"
    )
    material = models.ForeignKey(
        Material,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="unit_conversions",
        verbose_name="Áp dụng cho vật tư",
    )
    is_active = models.BooleanField(default=True, verbose_name="Đang áp dụng")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ngày cập nhật")

    class Meta:
        db_table = "unit_conversion"
        verbose_name = "Quy đổi đơn vị"
        verbose_name_plural = "Quy đổi đơn vị"
        constraints = [
            # Global: mỗi cặp (from_unit, to_unit) chỉ có 1 quy đổi
            models.UniqueConstraint(
                fields=["from_unit", "to_unit"],
                condition=models.Q(material__isnull=True),
                name="uq_unit_conversion_global",
            ),
            # Material-specific: mỗi cặp (from_unit, to_unit, material) là duy nhất
            models.UniqueConstraint(
                fields=["from_unit", "to_unit", "material"],
                condition=models.Q(material__isnull=False),
                name="uq_unit_conversion_material",
            ),
        ]

    def __str__(self):
        scope = f" ({self.material.code})" if self.material else " (toàn cục)"
        return f"1 {self.from_unit.code} = {self.factor} {self.to_unit.code}{scope}"
