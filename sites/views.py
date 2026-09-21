from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import serializers as drf_serializers
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from catalog.serializers import SimpleMaterialSerializer
from iam.permissions import IsAdmin

from .models import Site, SiteMaterialRequirement
from .serializers import (
    RequirementsUpdateSerializer,
    SettleSerializer,
    SiteRequirementRowSerializer,
    SiteSerializer,
)
from .services import build_requirement_rows, settle_site


def _django_validation_to_dict(exc):
    """Chuyển django ValidationError → dict cho DRF (trả 400)."""
    if hasattr(exc, "message_dict") and exc.message_dict:
        return exc.message_dict
    if exc.messages:
        return exc.messages[0]
    return str(exc)


@extend_schema(tags=["Site"])
@extend_schema_view(
    list=extend_schema(summary="Danh sách công trường (?status=active|completed|inactive|all)"),
    create=extend_schema(summary="Tạo công trường"),
    retrieve=extend_schema(summary="Chi tiết công trường"),
    update=extend_schema(summary="Cập nhật công trường"),
    partial_update=extend_schema(summary="Cập nhật một phần"),
    destroy=extend_schema(summary="Vô hiệu hóa công trường (status=inactive)"),
)
class SiteViewSet(viewsets.ModelViewSet):
    serializer_class = SiteSerializer
    pagination_class = None
    filter_backends = [SearchFilter]
    search_fields = ["code", "name"]

    def get_queryset(self):
        # Detail/update/actions: trả mọi site (kể cả completed/inactive).
        if self.action != "list":
            return Site.objects.all().order_by("name")
        status_param = self.request.query_params.get("status")
        qs = Site.objects.all().order_by("name")
        if status_param == "all":
            return qs
        if status_param in (
            Site.Status.ACTIVE,
            Site.Status.COMPLETED,
            Site.Status.INACTIVE,
        ):
            return qs.filter(status=status_param)
        # Mặc định: chỉ công trường đang hoạt động (giữ hành vi cũ của is_active)
        return qs.filter(status=Site.Status.ACTIVE)

    def get_permissions(self):
        if self.action in (
            "create",
            "update",
            "partial_update",
            "destroy",
            "settle",
        ):
            return [IsAdmin()]
        if self.action == "requirements" and self.request.method == "PUT":
            return [IsAdmin()]
        return [IsAuthenticated()]

    def perform_destroy(self, instance):
        instance.status = Site.Status.INACTIVE
        instance.save(update_fields=["status", "updated_at"])

    @extend_schema(
        summary="Bảng so sánh định mức vật tư vs tồn kho công trường",
        methods=["GET"],
        responses={200: SiteRequirementRowSerializer(many=True)},
    )
    @extend_schema(
        summary="Cập nhật định mức (bulk replace)",
        methods=["PUT"],
        request=RequirementsUpdateSerializer,
        responses={200: SiteRequirementRowSerializer(many=True)},
    )
    @action(detail=True, methods=["get", "put"], url_path="requirements")
    def requirements(self, request, pk=None):
        site = self.get_object()
        if request.method == "PUT":
            if site.status != Site.Status.ACTIVE:
                raise drf_serializers.ValidationError(
                    {"status": "Công trường đã đóng — không sửa định mức được."}
                )
            serializer = RequirementsUpdateSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            with transaction.atomic():
                site.material_requirements.all().delete()
                SiteMaterialRequirement.objects.bulk_create(
                    [
                        SiteMaterialRequirement(
                            site=site,
                            material=item["material"],
                            quantity=item["quantity"],
                            note=item.get("note", ""),
                        )
                        for item in serializer.validated_data["lines"]
                    ]
                )
        rows = build_requirement_rows(site)
        return Response(SiteRequirementRowSerializer(rows, many=True).data)

    @extend_schema(
        summary="Tất toán công trường — điều chuyển vật tư thừa/ngoài định mức về kho khác và đóng công trường",
        request=SettleSerializer,
    )
    @action(detail=True, methods=["post"])
    def settle(self, request, pk=None):
        site = self.get_object()
        serializer = SettleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            note = settle_site(
                site,
                serializer.validated_data["to_warehouse"],
                serializer.validated_data["lines"],
                request.user,
            )
        except DjangoValidationError as exc:
            raise drf_serializers.ValidationError(_django_validation_to_dict(exc))

        return Response(
            {
                "site": SiteSerializer(site).data,
                "outbound_note": {
                    "id": note.id,
                    "number": note.number,
                    "status": note.status,
                    "status_label": note.get_status_display(),
                    "warehouse": {
                        "id": note.warehouse_id,
                        "code": note.warehouse.code,
                        "name": note.warehouse.name,
                    },
                    "to_warehouse": {
                        "id": note.to_warehouse_id,
                        "code": note.to_warehouse.code,
                        "name": note.to_warehouse.name,
                    },
                    "lines": [
                        {
                            "material": SimpleMaterialSerializer(line.material).data,
                            "quantity": str(line.quantity),
                            "note": line.note,
                        }
                        for line in note.lines.select_related("material__unit")
                    ],
                },
            },
            status=status.HTTP_200_OK,
        )