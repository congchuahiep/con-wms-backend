from django.db import models


class Warehouse(models.Model):
    id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=20, unique=True, verbose_name="Mã kho")
    name = models.CharField(max_length=200, verbose_name="Tên kho")
    address = models.TextField(blank=True, verbose_name="Địa chỉ")
    note = models.TextField(blank=True, verbose_name="Ghi chú")
    latitude = models.DecimalField(
        max_digits=12, decimal_places=9, null=True, blank=True, verbose_name="Vĩ độ"
    )
    longitude = models.DecimalField(
        max_digits=12, decimal_places=9, null=True, blank=True, verbose_name="Kinh độ"
    )
    is_active = models.BooleanField(default=True, verbose_name="Đang hoạt động")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ngày cập nhật")

    class Meta:
        db_table = "warehouse"
        verbose_name = "Nhà kho"
        verbose_name_plural = "Nhà kho"

    def __str__(self):
        return f"{self.code} — {self.name}"
