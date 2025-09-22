"""
URL configuration for api project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from core.views import skus, sku_detail, inventory_adjust, inventory_by_hub
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.http import JsonResponse

@api_view(["GET"])
@permission_classes([AllowAny])
def ping(_req):
    return JsonResponse({"ok": True, "service": "tribestock-api"})

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    roles = list(request.user.groups.values_list("name", flat=True))
    return JsonResponse({"user": request.user.username, "roles": roles})

urlpatterns = [
    path("admin/", admin.site.urls),
    path("ping/", ping),  # public
    path("me/", me),      # protected
    path("auth/login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("skus/", skus),                     # GET list, POST create (Admin)
    path("skus/<int:pk>/", sku_detail),      # PATCH, DELETE (Admin)
    path("inventory/adjust/", inventory_adjust),  # POST IN/OUT
    path("inventory/by-hub/<int:hub_id>/", inventory_by_hub),  # GET stock

]
