from django.http import JsonResponse
from django.db import transaction
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Hub, SKU, HubInventory, InventoryLog
from .serializers import (
    HubSerializer, SKUSerializer,
    HubInventorySerializer, InventoryAdjustSerializer
)
from .roles import is_admin, is_hub_manager

def ping(_req):
    return JsonResponse({"ok": True, "service": "tribestock-api"})

    # --- SKUs (list/create, update/delete minimal) ---

@api_view(["GET","POST"])
@permission_classes([IsAuthenticated])
def skus(request):
    if request.method == "GET":
        qs = SKU.objects.all().order_by("sku_code")
        return Response(SKUSerializer(qs, many=True).data)
    # POST (Admin only)
    if not is_admin(request.user):
        return Response({"detail":"Admin only"}, status=403)
    ser = SKUSerializer(data=request.data)
    if ser.is_valid():
        ser.save()
        return Response(ser.data, status=201)
    return Response(ser.errors, status=400)

@api_view(["PATCH","DELETE"])
@permission_classes([IsAuthenticated])
def sku_detail(request, pk:int):
    try:
        sku = SKU.objects.get(pk=pk)
    except SKU.DoesNotExist:
        return Response({"detail":"Not found"}, status=404)
    if not is_admin(request.user):
        return Response({"detail":"Admin only"}, status=403)
    if request.method == "PATCH":
        ser = SKUSerializer(sku, data=request.data, partial=True)
        if ser.is_valid():
            ser.save()
            return Response(ser.data)
        return Response(ser.errors, status=400)
    # DELETE
    sku.delete()
    return Response(status=204)

# --- Inventory: adjust IN/OUT with logging, no negatives ---

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def inventory_adjust(request):
    """
    Body: { "hub":<id>, "sku":<id>, "direction":"IN"|"OUT", "qty":<int>, "note":"..." }
    Admin or HubManager only.
    """
    if not (is_admin(request.user) or is_hub_manager(request.user)):
        return Response({"detail":"Admin or HubManager only"}, status=403)

    ser = InventoryAdjustSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    hub = ser.validated_data["hub"]
    sku = ser.validated_data["sku"]
    direction = ser.validated_data["direction"]
    move = ser.validated_data["qty"]
    note = ser.validated_data.get("note","")

    with transaction.atomic():
        inv, _ = HubInventory.objects.select_for_update().get_or_create(hub=hub, sku=sku, defaults={"qty":0})
        before = inv.qty
        if direction == "IN":
            after = before + move
        else:
            # OUT
            if move > before:
                return Response({"detail": f"Insufficient stock: have {before}, tried to remove {move}"}, status=400)
            after = before - move
        inv.qty = after
        inv.save()
        InventoryLog.objects.create(
            hub=hub, sku=sku, direction=direction, delta=move,
            before_qty=before, after_qty=after, note=note, actor=request.user
        )

    return Response({"hub": hub.id, "sku": sku.id, "direction": direction, "moved": move, "after_qty": after}, status=200)

# --- (Nice to have) view stock for a hub ---

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def inventory_by_hub(request, hub_id:int):
    try:
        hub = Hub.objects.get(pk=hub_id)
    except Hub.DoesNotExist:
        return Response({"detail":"Hub not found"}, status=404)
    inv = HubInventory.objects.filter(hub=hub).select_related("sku","hub").order_by("sku__sku_code")
    return Response(HubInventorySerializer(inv, many=True).data)