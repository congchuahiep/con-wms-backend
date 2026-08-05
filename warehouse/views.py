from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated

from iam.permissions import IsAdmin

from .filters import WarehouseFilter
from .models import Warehouse
from .serializers import WarehouseSerializer


@extend_schema(tags=["Warehouse"])
@extend_schema_view(
    list=extend_schema(
        summary="Danh sách nhà kho",
        description="Trả về danh sách nhà kho đang hoạt động.",
    ),
    create=extend_schema(
        summary="Tạo nhà kho mới",
        description="Tạo một nhà kho mới. Chỉ admin được phép.",
    ),
    retrieve=extend_schema(
        summary="Chi tiết nhà kho",
        description="Xem chi tiết một nhà kho.",
    ),
    update=extend_schema(
        summary="Cập nhật nhà kho",
        description="Cập nhật thông tin nhà kho. Chỉ admin được phép.",
    ),
    partial_update=extend_schema(
        summary="Cập nhật một phần nhà kho",
        description="Cập nhật một phần thông tin nhà kho. Chỉ admin được phép.",
    ),
    destroy=extend_schema(
        summary="Vô hiệu hóa nhà kho",
        description="Soft delete, đặt is_active=False. Chỉ admin được phép.",
    ),
)
class WarehouseViewSet(viewsets.ModelViewSet):
    serializer_class = WarehouseSerializer
    pagination_class = None
    filter_backends = [SearchFilter]
    search_fields = ["code", "name"]
    filterset_class = WarehouseFilter

    def get_queryset(self):
        return Warehouse.objects.all().order_by("name")

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAdmin()]
        return [IsAuthenticated()]

    def perform_destroy(self, instance):
        """Soft delete: set is_active=False instead of hard delete."""
        instance.is_active = False
        instance.save()
