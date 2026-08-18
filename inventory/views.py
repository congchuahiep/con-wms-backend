from django.db.models import OuterRef, Subquery, Sum
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import (
    OpenApiParameter,
    extend_schema,
    extend_schema_view,
)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from catalog.models import Material
from config.pagination import StandardPageNumberPagination
from iam.permissions import IsAdminOrStorekeeper
from warehouse.models import Warehouse

from . import services
from .filters import InboundNoteFilter, StockBalanceFilter, StockMovementFilter
from .models import InboundNote, StockMovement
from .serializers import (
    InboundNoteListSerializer,
    InboundNoteSerializer,
    StockBalanceSerializer,
    StockMovementSerializer,
    VoidInboundNoteSerializer,
)


@extend_schema(tags=["InboundNote"])
@extend_schema_view(
    list=extend_schema(
        summary="Danh sách phiếu nhập",
        description="Danh sách phiếu nhập phân trang. Lọc theo loại, trạng thái, kho, NCC, ngày.",
    ),
    create=extend_schema(
        summary="Tạo phiếu nhập (nháp)",
        description="Tạo phiếu nháp kèm dòng vật tư. Phiếu nháp chưa ảnh hưởng tồn kho.",
    ),
    retrieve=extend_schema(summary="Chi tiết phiếu nhập"),
    update=extend_schema(
        summary="Cập nhật phiếu nháp",
        description="Chỉ áp dụng cho phiếu nháp. Dòng cũ bị thay bằng danh sách mới.",
    ),
    partial_update=extend_schema(
        summary="Cập nhật một phần phiếu nháp",
        description="Chỉ áp dụng cho phiếu nháp.",
    ),
    destroy=extend_schema(
        summary="Xóa phiếu nháp",
        description="Xóa cứng phiếu nháp. Phiếu đã chốt phải dùng /void/.",
    ),
    post=extend_schema(
        summary="Chốt phiếu — ghi sổ kho",
        description="Mỗi dòng sinh 1 dòng sổ kho (+tồn), phiếu chuyển sang posted và bất biến.",
    ),
    void=extend_schema(
        summary="Hủy phiếu — dòng sổ kho ngược dấu",
        description="Ghi dòng ngược dấu cho từng dòng gốc (−tồn), bắt buộc lý do.",
        request=VoidInboundNoteSerializer,
    ),
)
class InboundNoteViewSet(viewsets.ModelViewSet):
    serializer_class = InboundNoteSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = InboundNoteFilter
    search_fields = ["number", "note"]

    def get_queryset(self):
        return (
            InboundNote.objects.select_related(
                "warehouse", "supplier", "created_by", "voided_by"
            )
            .prefetch_related("lines__material")
            .order_by("-date", "-id")
        )

    def get_serializer_class(self):
        if self.action == "list":
            return InboundNoteListSerializer
        return InboundNoteSerializer

    def get_permissions(self):
        if self.action in (
            "create",
            "update",
            "partial_update",
            "destroy",
            "post",
            "void",
        ):
            return [IsAdminOrStorekeeper()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        note_date = serializer.validated_data.get("date") or timezone.localdate()
        serializer.save(
            created_by=self.request.user,
            number=services.generate_inbound_note_number(note_date),
        )

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.is_draft:
            return Response(
                {
                    "detail": "Phiếu đã chốt/hủy không được sửa. "
                    "Hãy hủy phiếu và lập phiếu mới."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.is_draft:
            return Response(
                {
                    "detail": "Phiếu đã chốt/hủy không được sửa. "
                    "Hãy hủy phiếu và lập phiếu mới."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.is_draft:
            return Response(
                {"detail": "Chỉ phiếu nháp mới xóa được. Phiếu đã chốt dùng /void/."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"])
    def post(self, request, pk=None):
        """Chốt phiếu → ghi dòng sổ kho (+tồn)."""
        note = self.get_object()
        note.post(request.user)
        return Response(self.get_serializer(note).data)

    @action(detail=True, methods=["post"])
    def void(self, request, pk=None):
        """Hủy phiếu đã chốt → dòng sổ kho ngược dấu (−tồn)."""
        note = self.get_object()
        serializer = VoidInboundNoteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        note.void(serializer.validated_data["reason"], request.user)
        return Response(self.get_serializer(note).data)


class StockMovementPagination(StandardPageNumberPagination):
    page_size = 50


@extend_schema(tags=["Stock"])
@extend_schema_view(
    list=extend_schema(
        summary="Tồn kho hiện tại",
        description=(
            "Tồn = SUM(quantity) các dòng sổ kho theo (kho, vật tư). "
            "Read-only — không có API ghi trực tiếp."
        ),
        parameters=[
            OpenApiParameter(name="warehouse", type=int),
            OpenApiParameter(name="material", type=int),
            OpenApiParameter(name="category", type=int),
            OpenApiParameter(name="has_stock", type=bool),
            OpenApiParameter(name="search", type=str),
        ],
    ),
)
class StockBalanceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = StockBalanceSerializer
    pagination_class = None
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = StockBalanceFilter
    search_fields = ["material__code", "material__name"]

    def get_queryset(self):
        last_purchase_price = (
            StockMovement.objects.filter(
                warehouse_id=OuterRef("warehouse_id"),
                material_id=OuterRef("material_id"),
                movement_type=StockMovement.Type.INBOUND_PURCHASE_FROM_SUPPLIER,
                unit_price__isnull=False,
            )
            .order_by("-date", "-id")
            .values("unit_price")[:1]
        )
        return (
            StockMovement.objects.values("warehouse_id", "material_id")
            .annotate(
                quantity=Sum("quantity"),
                last_purchase_price=Subquery(last_purchase_price),
            )
            .order_by("warehouse_id", "material_id")
        )

    def list(self, request, *args, **kwargs):
        rows = list(self.filter_queryset(self.get_queryset()))
        materials = {
            m.id: m
            for m in Material.objects.filter(
                id__in=[r["material_id"] for r in rows]
            ).select_related("unit")
        }
        warehouses = {
            w.id: w
            for w in Warehouse.objects.filter(id__in=[r["warehouse_id"] for r in rows])
        }
        serializer = StockBalanceSerializer(
            rows,
            many=True,
            context={"materials": materials, "warehouses": warehouses},
        )
        return Response(serializer.data)


@extend_schema(tags=["Stock"])
@extend_schema_view(
    list=extend_schema(
        summary="Sổ kho — lịch sử dòng ghi",
        description=(
            "Lịch sử dòng sổ kho bất biến. Mặc định ẩn dòng reversal "
            "(?originals_only=false để xem cả dòng ngược dấu)."
        ),
    ),
    retrieve=extend_schema(summary="Chi tiết dòng sổ kho"),
)
class StockMovementViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = StockMovementSerializer
    pagination_class = StockMovementPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = StockMovementFilter
    search_fields = ["material__code", "material__name", "inbound_note__number"]

    def get_queryset(self):
        qs = StockMovement.objects.select_related(
            "material", "warehouse", "inbound_note", "created_by"
        )
        originals_only = self.request.query_params.get("originals_only", "true")
        if originals_only.lower() != "false":
            qs = qs.filter(reversal_of__isnull=True)
        return qs.order_by("-date", "-id")
