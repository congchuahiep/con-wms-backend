from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated

from iam.permissions import IsAdmin

from .filters import SupplierFilter
from .models import Supplier
from .serializers import SupplierSerializer


@extend_schema(tags=["Supplier"])
@extend_schema_view(
    list=extend_schema(
        summary="Danh sách nhà cung cấp",
        description="Trả về danh sách nhà cung cấp đang hợp tác.",
    ),
    create=extend_schema(
        summary="Tạo nhà cung cấp mới",
        description="Tạo một nhà cung cấp mới. Chỉ admin được phép.",
    ),
    retrieve=extend_schema(
        summary="Chi tiết nhà cung cấp",
        description="Xem chi tiết một nhà cung cấp.",
    ),
    update=extend_schema(
        summary="Cập nhật nhà cung cấp",
        description="Cập nhật thông tin nhà cung cấp. Chỉ admin được phép.",
    ),
    partial_update=extend_schema(
        summary="Cập nhật một phần nhà cung cấp",
        description="Cập nhật một phần thông tin nhà cung cấp. Chỉ admin được phép.",
    ),
    destroy=extend_schema(
        summary="Vô hiệu hóa nhà cung cấp",
        description="Soft delete, đặt is_active=False. Chỉ admin được phép.",
    ),
)
class SupplierViewSet(viewsets.ModelViewSet):
    serializer_class = SupplierSerializer
    pagination_class = None
    filter_backends = [SearchFilter]
    search_fields = ["code", "name"]
    filterset_class = SupplierFilter

    def get_queryset(self):
        return Supplier.objects.all().order_by("code")

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAdmin()]
        return [IsAuthenticated()]

    def perform_destroy(self, instance):
        """Soft delete: set is_active=False instead of hard delete."""
        instance.is_active = False
        instance.save()
