from django.conf import settings
from django.db import models


class Site(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Đang hoạt động"
        COMPLETED = "completed", "Đã hoàn thành"
        INACTIVE = "inactive", "Ngừng hoạt động"

    id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=20, unique=True, verbose_name="Mã công trường")
    name = models.CharField(max_length=200, verbose_name="Tên công trường")
    manager = models.CharField(max_length=100, blank=True, verbose_name="Người phụ trách")
    phone = models.CharField(max_length=20, blank=True, verbose_name="SĐT")
    address = models.TextField(blank=True, verbose_name="Địa chỉ")
    note = models.TextField(blank=True, verbose_name="Ghi chú")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name="Trạng thái",
    )
    settled_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Thời điểm tất toán"
    )
    settled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="settled_sites",
        verbose_name="Người tất toán",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ngày cập nhật")

    class Meta:
        db_table = "site"
        verbose_name = "Công trường"
        verbose_name_plural = "Công trường"

    def __str__(self):
        return f"{self.code} — {self.name}"


class SiteMaterialRequirement(models.Model):
    """Định mức vật tư công trường — mốc so sánh với tồn kho công trường.

    Không giới hạn việc nhập thêm vật tư ngoài danh sách này; bảng này chỉ
    dùng để so sánh "công trường cần bao nhiêu / kho đang có bao nhiêu"
    và tính phần trả về khi tất toán.
    """

    id = models.BigAutoField(primary_key=True)
    site = models.ForeignKey(
        Site,
        on_delete=models.PROTECT,
        related_name="material_requirements",
        verbose_name="Công trường",
    )
    material = models.ForeignKey(
        "catalog.Material",
        on_delete=models.PROTECT,
        related_name="site_material_requirements",
        verbose_name="Vật tư",
    )
    quantity = models.DecimalField(
        max_digits=14, decimal_places=3, verbose_name="Số lượng định mức"
    )
    note = models.TextField(blank=True, verbose_name="Ghi chú")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ngày cập nhật")

    class Meta:
        db_table = "site_material_requirement"
        verbose_name = "Định mức vật tư công trường"
        verbose_name_plural = "Định mức vật tư công trường"
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(
                fields=["site", "material"],
                name="uq_smr_site_material",
            ),
            models.CheckConstraint(
                condition=models.Q(quantity__gt=0),
                name="ck_smr_quantity_positive",
            ),
        ]

    def __str__(self):
        return f"{self.site.code} — {self.material.code} × {self.quantity}"