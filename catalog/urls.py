from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    MaterialCategoryViewSet,
    MaterialViewSet,
    UnitConversionViewSet,
    UnitViewSet,
)

router = DefaultRouter()
router.register("categories", MaterialCategoryViewSet, basename="category")
router.register("units", UnitViewSet, basename="unit")
router.register("materials", MaterialViewSet, basename="material")

urlpatterns = router.urls

# Flat routes cho UnitConversion (PUT/DELETE)
urlpatterns += [
    path(
        "unit-conversions/<int:pk>/",
        UnitConversionViewSet.as_view({"put": "update", "patch": "partial_update", "delete": "destroy"}),
        name="unit-conversion-detail",
    ),
]
