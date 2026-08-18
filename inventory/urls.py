from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import InboundNoteViewSet, StockBalanceViewSet, StockMovementViewSet

router = DefaultRouter()
router.register("inbound-notes", InboundNoteViewSet, basename="inbound-note")
router.register("stock/movements", StockMovementViewSet, basename="stock-movement")

# Stock balance chỉ có list, không có detail — dùng path() trực tiếp để
# tránh route "stock/{pk}/" nuốt "stock/movements/".
urlpatterns = [
    path("stock/", StockBalanceViewSet.as_view({"get": "list"}), name="stock-list"),
] + router.urls
