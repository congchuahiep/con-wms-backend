from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Site
from .services import ensure_site_warehouse


@receiver(post_save, sender=Site)
def create_site_warehouse(sender, instance, created, **kwargs):
    """Tạo kho công trường ngay khi tạo Site mới (chỉ khi `created=True`)."""
    if created:
        ensure_site_warehouse(instance)