"""
Root URL configuration for api project.
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse


def root(_req):
    return JsonResponse({
        "ok": True,
        "service": "tribestock-api",
        "versions": ["v1"],
        "health": "/api/v1/ping/"
    })


urlpatterns = [
    path("admin/", admin.site.urls, name="admin"),
    # Versioned API namespace
    path("api/v1/", include(("api.urls_v1", "v1"), namespace="v1")),
    # Root fallback
    path("", root, name="root"),
]
