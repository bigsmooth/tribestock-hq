from rest_framework import serializers
from .models import Hub, SKU, Inventory, InventoryLog


class HubSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hub
        fields = ["id", "code", "name", "city", "country", "active", "created_at"]


class SKUSerializer(serializers.ModelSerializer):
    class Meta:
        model = SKU
        fields = ["id", "sku_code", "name", "color", "size", "barcode", "active", "created_at"]


class InventorySerializer(serializers.ModelSerializer):
    sku_id = serializers.IntegerField(source="sku.id", read_only=True)
    sku_code = serializers.CharField(source="sku.sku_code", read_only=True)
    name = serializers.CharField(source="sku.name", read_only=True)

    class Meta:
        model = Inventory
        fields = ["sku_id", "sku_code", "name", "quantity"]


class InventoryAdjustSerializer(serializers.Serializer):
    sku_id = serializers.IntegerField()
    hub_id = serializers.IntegerField()
    action = serializers.ChoiceField(choices=["IN", "OUT"])
    quantity = serializers.IntegerField(min_value=1)

    def validate(self, data):
        # Normalize action
        data["action"] = data["action"].upper()
        return data


class InventoryLogSerializer(serializers.ModelSerializer):
    hub_code = serializers.CharField(source="hub.code", read_only=True)
    sku_code = serializers.CharField(source="sku.sku_code", read_only=True)
    actor_username = serializers.CharField(source="actor.username", read_only=True)

    class Meta:
        model = InventoryLog
        fields = [
            "id",
            "created_at",
            "hub", "hub_code",
            "sku", "sku_code",
            "direction", "delta",
            "before_qty", "after_qty",
            "note", "actor", "actor_username",
        ]
