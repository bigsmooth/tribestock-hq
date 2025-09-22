from django.http import JsonResponse
from django.db import transaction
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status  # 👈 important
from .models import Hub, SKU, HubInventory, InventoryLog
from .serializers import (
    HubSerializer, SKUSerializer,
    HubInventorySerializer, InventoryAdjustSerializer
)
from .roles import is_admin, is_hub_manager

# --- public health check
@api_view(["GET"])
@permission_classes([AllowAny])
def ping(_req):
    return JsonResponse({"ok": True, "service": "tribestock-api"})

# --- whoami (protected)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    roles = list(request.user.groups.values_list("name", flat=True))
    return JsonResponse({"user": request.user.username, "roles": roles})

# --- SKUs (list + create)
@api_view(["GET","POST"])
@permission_classes([IsAuthenticated])
def skus(request):
    if request.method == "GET":
        qs = SKU.objects.all().order_by("sku_code")
        return Response(SKUSerializer(qs, many=True).data, status=status.HTTP_200_OK)
    if not is_admin(request.user):
        return Response({"detail":"Admin only"}, status=status.HTTP_403_FORBIDDEN)
    ser = SKUSerializer(data=request.data)
    if ser.is_valid():
        ser.save()
        return Response(ser.data, status=status.HTTP_201_CREATED)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

# --- SKU detail (update/delete)
@api_view(["PATCH","DELETE"])
@permission_classes([IsAuthenticated])
def sku_detail(request, pk:int):
    try:
        sku = SKU.objects.get(pk=pk)
    except SKU.DoesNotExist:
        return Response({"detail":"Not found"}, status=status.HTTP_404_NOT_FOUND)
    if not is_admin(request.user):
        return Response({"detail":"Admin only"}, status=status.HTTP_403_FORBIDDEN)
    if request.method == "PATCH":
        ser = SKUSerializer(sku, data=request.data, partial=True)
        if ser.is_valid():
            ser.save()
            return Response(ser.data, status=status.HTTP_200_OK)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
    sku.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

# --- Inventory adjust (IN/OUT)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def inventory_adjust(request):
    if not (is_admin(request.user) or is_hub_manager(request.user)):
        return Response({"detail":"Admin or HubManager only"}, status=status.HTTP_403_FORBIDDEN)

    ser = InventoryAdjustSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    hub = ser.validated_data["hub"]
    sku = ser.validated_data["sku"]
    direction = ser.validated_data["direction"]
    move = ser.validated_data["qty"]
    note = ser.validated_data.get("note","")

    with transaction.atomic():
        inv, _ = HubInventory.objects.select_for_update().get_or_create(
            hub=hub, sku=sku, defaults={"qty": 0}
        )
        before = inv.qty
        if direction == "IN":
            after = before + move
        else:
            if move > before:
                return Response(
                    {"detail": f"Insufficient stock: have {before}, tried to remove {move}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            after = before - move
        inv.qty = after
        inv.save()
        InventoryLog.objects.create(
            hub=hub, sku=sku, direction=direction, delta=move,
            before_qty=before, after_qty=after, note=note, actor=request.user
        )

    return Response(
        {"hub": hub.id, "sku": sku.id, "direction": direction, "moved": move, "after_qty": after},
        status=status.HTTP_200_OK,
    )

# --- Inventory by hub
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def inventory_by_hub(request, hub_id:int):
    try:
        hub = Hub.objects.get(pk=hub_id)
    except Hub.DoesNotExist:
        return Response({"detail":"Hub not found"}, status=status.HTTP_404_NOT_FOUND)
    inv = HubInventory.objects.filter(hub=hub).select_related("sku","hub").order_by("sku__sku_code")
    return Response(HubInventorySerializer(inv, many=True).data, status=status.HTTP_200_OK)
