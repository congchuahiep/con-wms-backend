from django.db.models.deletion import ProtectedError
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from iam.permissions import IsAdminOrStorekeeper

from .models import Material, MaterialCategory, Unit, UnitConversion
from .serializers import (
    DetailedUnitSerializer,
    MaterialCategoryFlatSerializer,
    MaterialCategorySerializer,
    MaterialDetailSerializer,
    MaterialSerializer,
    UnitConversionSerializer,
    UnitSerializer,
)


@extend_schema(tags=["MaterialCategory"])
@extend_schema_view(
    list=extend_schema(
        summary="Danh sách danh mục",
        description=(
            "Mặc định trả về cây lồng đệ quy (chỉ node gốc). "
            "Dùng `?flat=true` để lấy danh sách phẳng kèm `depth` cho select box."
        ),
    ),
    create=extend_schema(summary="Tạo danh mục mới"),
    retrieve=extend_schema(summary="Chi tiết danh mục"),
    update=extend_schema(summary="Cập nhật danh mục"),
    partial_update=extend_schema(summary="Cập nhật một phần danh mục"),
    destroy=extend_schema(summary="Xóa danh mục"),
)
class MaterialCategoryViewSet(viewsets.ModelViewSet):
    pagination_class = None
    filter_backends = [SearchFilter]
    search_fields = ["code", "name"]

    def get_queryset(self):
        qs = MaterialCategory.objects.all()
        if self.action == "list" and self.request.query_params.get("flat") == "true":
            return qs.select_related("parent").order_by("parent__id", "code")
        if self.action == "list":
            return qs.filter(parent__isnull=True).order_by("code")
        return qs.order_by("code")

    def get_serializer_class(self):
        if self.action == "list" and self.request.query_params.get("flat") == "true":
            return MaterialCategoryFlatSerializer
        return MaterialCategorySerializer

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAdminOrStorekeeper()]
        return [IsAuthenticated()]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        try:
            self.perform_destroy(instance)
        except ProtectedError as e:
            # FK PROTECT: danh mục đang được Material hoặc category con tham chiếu
            blocked = [f"{obj._meta.verbose_name} - {obj}" for obj in e.protected_objects]
            return Response(
                {
                    "detail": "Không thể xóa vì có vật tư hoặc danh mục con đang tham chiếu đến nó.",
                    "blocked_by": blocked,
                },
                status=status.HTTP_409_CONFLICT,
            )
        return Response(data)


@extend_schema(tags=["Unit"])
@extend_schema_view(
    list=extend_schema(summary="Danh sách đơn vị"),
    create=extend_schema(summary="Tạo đơn vị mới"),
    retrieve=extend_schema(
        summary="Chi tiết đơn vị (kèm danh sách quy đổi)",
        description="Trả về thông tin đơn vị + danh sách quy đổi (gồm cả chiều ngược với global).",
        responses={200: DetailedUnitSerializer()},
    ),
    update=extend_schema(summary="Cập nhật đơn vị"),
    partial_update=extend_schema(summary="Cập nhật một phần đơn vị"),
    destroy=extend_schema(summary="Xóa đơn vị"),
    create_conversion=extend_schema(
        summary="Tạo quy đổi mới cho đơn vị",
        description="from_unit tự động là unit trong URL. Body: toUnitId, factor, materialId (bắt buộc nếu unit là material).",
        request=UnitConversionSerializer,
        responses={201: UnitConversionSerializer},
    ),
)
class UnitViewSet(viewsets.ModelViewSet):
    serializer_class = UnitSerializer
    pagination_class = None

    def get_queryset(self):
        return Unit.objects.all().order_by("code")

    def get_permissions(self):
        if self.action in (
            "create",
            "create_conversion",
            "update",
            "partial_update",
            "destroy",
        ):
            return [IsAdminOrStorekeeper()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return DetailedUnitSerializer
        return super().get_serializer_class()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        try:
            self.perform_destroy(instance)
        except ProtectedError as e:
            # FK PROTECT: unit đang được Material hoặc UnitConversion tham chiếu
            blocked = [f"{obj._meta.verbose_name} - {obj}" for obj in e.protected_objects]
            return Response(
                {
                    "detail": "Không thể xóa vì đang được tham chiếu.",
                    "blocked_by": blocked,
                },
                status=status.HTTP_409_CONFLICT,
            )
        return Response(data)

    @action(detail=True, methods=["post"], url_path="conversions")
    def create_conversion(self, request, *_args, **_kwargs):
        unit = self.get_object()

        data = request.data.copy()
        data.setdefault("from_unit_id", unit.pk)
        if "material_id" not in data and "materialId" not in request.data:
            data["material_id"] = None

        serializer = UnitConversionSerializer(data=data, context={"from_unit": unit})
        serializer.is_valid(raise_exception=True)
        conversion = serializer.save()

        return Response(
            UnitConversionSerializer(conversion).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=["UnitConversion"])
@extend_schema_view(
    update=extend_schema(summary="Cập nhật quy đổi"),
    partial_update=extend_schema(summary="Cập nhật một phần quy đổi"),
    destroy=extend_schema(summary="Xóa quy đổi"),
)
class UnitConversionViewSet(
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = UnitConversionSerializer

    def get_queryset(self):
        return UnitConversion.objects.select_related("from_unit", "to_unit", "material")

    def get_permissions(self):
        return [IsAdminOrStorekeeper()]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        try:
            self.perform_destroy(instance)
        except ProtectedError as e:
            # FK PROTECT: UnitConversion đang được tham chiếu (dù hiếm)
            blocked = [f"{obj._meta.verbose_name} - {obj}" for obj in e.protected_objects]
            return Response(
                {
                    "detail": "Không thể xóa vì đang được tham chiếu.",
                    "blocked_by": blocked,
                },
                status=status.HTTP_409_CONFLICT,
            )
        return Response(data)


@extend_schema(tags=["Material"])
@extend_schema_view(
    list=extend_schema(
        summary="Danh sách vật tư", description="Trả về danh sách vật tư có phân trang."
    ),
    create=extend_schema(
        summary="Tạo vật tư mới",
        description=(
            "Admin hoặc Thủ kho đều có thể tạo. Nếu `unitId` thuộc loại `material`, "
            "có thể gửi kèm `conversions` để tạo quy đổi atomic."
        ),
        request=MaterialSerializer,
        responses={201: MaterialSerializer},
    ),
    retrieve=extend_schema(
        summary="Chi tiết vật tư (kèm quy đổi)",
        responses={200: MaterialDetailSerializer},
    ),
    update=extend_schema(
        summary="Cập nhật vật tư",
        request=MaterialSerializer,
        responses={200: MaterialSerializer},
    ),
    partial_update=extend_schema(
        summary="Cập nhật một phần vật tư",
        request=MaterialSerializer,
        responses={200: MaterialSerializer},
    ),
    destroy=extend_schema(summary="Xóa vật tư"),
)
class MaterialViewSet(viewsets.ModelViewSet):
    serializer_class = MaterialSerializer
    filter_backends = [SearchFilter]
    search_fields = ["code", "name"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return MaterialDetailSerializer
        return MaterialSerializer

    def get_queryset(self):
        qs = Material.objects.select_related("category", "unit")
        category = self.request.query_params.get("category")
        if category:
            qs = qs.filter(category_id=category)
        return qs.order_by("code")

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAdminOrStorekeeper()]
        return [IsAuthenticated()]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        try:
            self.perform_destroy(instance)
        except ProtectedError as e:
            # FK PROTECT: Material đang được UnitConversion (material-specific) tham chiếu
            blocked = [f"{obj._meta.verbose_name} - {obj}" for obj in e.protected_objects]
            return Response(
                {
                    "detail": "Không thể xóa vì đang được tham chiếu.",
                    "blocked_by": blocked,
                },
                status=status.HTTP_409_CONFLICT,
            )
        return Response(data)
