# api/urls_v1.py
from django.urls import path
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from core.views import skus, sku_detail, inventory_adjust, inventory_by_hub

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

urlpatterns = [
    path("ping/", ping, name="ping"),
    path("auth/login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("me/", me, name="me"),
    path("skus/", skus, name="skus"),
    path("skus/<int:pk>/", sku_detail, name="sku_detail"),
    path("inventory/adjust/", inventory_adjust, name="inventory_adjust"),
    path("inventory/by-hub/<int:hub_id>/", inventory_by_hub, name="inventory_by_hub"),
]
