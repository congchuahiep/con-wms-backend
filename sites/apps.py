from django.apps import AppConfig


class SitesConfig(AppConfig):
    name = "sites"

    def ready(self):
        from . import (
            signals,  # noqa: F401 — đăng ký post_save auto-create kho công trường
        )
