from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    DraftNoteCountView,
    InboundNoteViewSet,
    OutboundNoteViewSet,
    StockBalanceViewSet,
    StockMovementViewSet,
    StocktakeNoteViewSet,
)

router = DefaultRouter()
router.register("inbound-notes", InboundNoteViewSet, basename="inbound-note")
router.register("outbound-notes", OutboundNoteViewSet, basename="outbound-note")
router.register("stocktake-notes", StocktakeNoteViewSet, basename="stocktake-note")
router.register("stock/movements", StockMovementViewSet, basename="stock-movement")

urlpatterns = [
    path("stock/", StockBalanceViewSet.as_view({"get": "list"}), name="stock-list"),
    path("draft-count/", DraftNoteCountView.as_view(), name="draft-count"),
] + router.urls