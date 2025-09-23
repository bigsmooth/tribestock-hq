# api/urls_v1.py
from django.urls import path
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.schemas import get_schema_view

from core.views import (
    skus,
    sku_detail,
    inventory_adjust,
    inventory_by_hub,
    hubs,
    inventory_logs,
)

app_name = "v1"

@api_view(["GET"])
@permission_classes([AllowAny])
def ping(_req):
    return JsonResponse({"ok": True, "service": "tribestock-api", "version": "v1"})

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    roles = list(request.user.groups.values_list("name", flat=True))
    return JsonResponse({"user": request.user.username, "roles": roles})

schema_view = get_schema_view(
    title="Tribestock API",
    version="1.0.0",
    description="Inventory & shipments for TTT hubs",
    public=True,
    permission_classes=[AllowAny],
)

urlpatterns = [
    path("ping/", ping, name="ping"),
    path("schema/", schema_view, name="schema"),

    # Auth
    path("auth/login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # Core
    path("me/", me, name="me"),
    path("hubs/", hubs, name="hubs"),
    path("skus/", skus, name="skus"),
    path("skus/<int:pk>/", sku_detail, name="sku_detail"),

    # Inventory
    path("inventory/by-hub/<int:hub_id>/", inventory_by_hub, name="inventory_by_hub"),
    path("inventory/adjust/", inventory_adjust, name="inventory_adjust"),

    # Logs
    path("logs/", inventory_logs, name="inventory_logs"),
]
