from django.db import models


class Supplier(models.Model):
    id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=20, unique=True, verbose_name="Mã NCC")
    name = models.CharField(max_length=200, verbose_name="Tên NCC")
    tax_code = models.CharField(
        max_length=20, unique=True, blank=True, verbose_name="Mã số thuế"
    )
    contact_person = models.CharField(
        max_length=100, blank=True, verbose_name="Người liên hệ"
    )
    phone = models.CharField(max_length=20, blank=True, verbose_name="SĐT")
    email = models.EmailField(blank=True, verbose_name="Email")
    address = models.TextField(blank=True, verbose_name="Địa chỉ")
    note = models.TextField(blank=True, verbose_name="Ghi chú")
    is_active = models.BooleanField(default=True, verbose_name="Đang hợp tác")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ngày cập nhật")

    class Meta:
        db_table = "supplier"
        verbose_name = "Nhà cung cấp"
        verbose_name_plural = "Nhà cung cấp"

    def __str__(self):
        return f"{self.code} — {self.name}"
