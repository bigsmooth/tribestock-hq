# core/views.py
from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Hub, SKU, Inventory, InventoryLog
from .serializers import (
    HubSerializer,
    SKUSerializer,
    InventorySerializer,
    InventoryAdjustSerializer,
    InventoryLogSerializer,
)


def _is_admin(user) -> bool:
    return user.is_superuser or user.groups.filter(name="Admin").exists()


# -----------------------------
# Hubs
# -----------------------------
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def hubs(request):
    qs = Hub.objects.order_by("code", "name")
    return Response(HubSerializer(qs, many=True).data, status=200)


# -----------------------------
# SKUs
# -----------------------------
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def skus(request):
    if request.method == "GET":
        qs = SKU.objects.order_by("sku_code")
        return Response(SKUSerializer(qs, many=True).data)

    if not _is_admin(request.user):
        return Response({"detail": "Admin only"}, status=status.HTTP_403_FORBIDDEN)

    ser = SKUSerializer(data=request.data)
    if not ser.is_valid():
        return Response(ser.errors, status=400)
    obj = ser.save()
    return Response(SKUSerializer(obj).data, status=201)


@api_view(["PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def sku_detail(request, pk: int):
    sku = get_object_or_404(SKU, pk=pk)

    if request.method == "PATCH":
        if not _is_admin(request.user):
            return Response({"detail": "Admin only"}, status=403)
        ser = SKUSerializer(sku, data=request.data, partial=True)
        if not ser.is_valid():
            return Response(ser.errors, status=400)
        ser.save()
        return Response(ser.data)

    if not _is_admin(request.user):
        return Response({"detail": "Admin only"}, status=403)
    sku.delete()
    return Response(status=204)


# -----------------------------
# Inventory
# -----------------------------
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def inventory_by_hub(request, hub_id: int):
    rows = (
        Inventory.objects.filter(hub_id=hub_id)
        .select_related("sku")
        .order_by("sku__name")
    )
    return Response(InventorySerializer(rows, many=True).data, status=200)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def inventory_adjust(request):
    """
    Body JSON:
    {
      "sku_id": 3,
      "hub_id": 7,
      "action": "IN" | "OUT",
      "quantity": 5,
      "note": "optional"
    }
    """
    ser = InventoryAdjustSerializer(data=request.data)
    if not ser.is_valid():
        return Response(ser.errors, status=400)

    sku_id = ser.validated_data["sku_id"]
    hub_id = ser.validated_data["hub_id"]
    qty = ser.validated_data["quantity"]
    action = ser.validated_data["action"]
    note = ser.validated_data.get("note", "")

    sku = get_object_or_404(SKU, pk=sku_id)
    get_object_or_404(Hub, pk=hub_id)  # ensure hub exists

    inv, _ = Inventory.objects.select_for_update().get_or_create(
        hub_id=hub_id, sku=sku, defaults={"quantity": 0}
    )

    before = inv.quantity
    if action == "IN":
        inv.quantity = before + qty
        direction = InventoryLog.IN
        delta = qty
    else:
        if before - qty < 0:
            return Response({"detail": "Insufficient stock"}, status=400)
        inv.quantity = before - qty
        direction = InventoryLog.OUT
        delta = qty

    inv.save()

    InventoryLog.objects.create(
        hub_id=hub_id,
        sku=sku,
        direction=direction,
        delta=delta,
        before_qty=before,
        after_qty=inv.quantity,
        note=note,
        actor=request.user if request.user.is_authenticated else None,
    )

    return Response(
        {"ok": True, "hub_id": hub_id, "sku_id": sku_id, "quantity": inv.quantity},
        status=200,
    )


# -----------------------------
# Logs
# -----------------------------
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def inventory_logs(request):
    hub_id = request.GET.get("hub_id")
    sku_id = request.GET.get("sku_id")
    try:
        limit = int(request.GET.get("limit", 50))
    except ValueError:
        limit = 50
    limit = min(max(limit, 1), 200)

    qs = InventoryLog.objects.select_related("hub", "sku", "actor").order_by("-created_at")
    if hub_id:
        qs = qs.filter(hub_id=hub_id)
    if sku_id:
        qs = qs.filter(sku_id=sku_id)
    qs = qs[:limit]

    return Response(InventoryLogSerializer(qs, many=True).data, status=200)
