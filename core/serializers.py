from rest_framework import serializers
from .models import Hub, SKU, HubInventory, InventoryLog

class HubSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hub
        fields = ["id","name","code","city","country","active","created_at"]

class SKUSerializer(serializers.ModelSerializer):
    class Meta:
        model = SKU
        fields = ["id","name","sku_code","color","size","barcode","active","created_at"]

class HubInventorySerializer(serializers.ModelSerializer):
    hub_code = serializers.CharField(source="hub.code", read_only=True)
    sku_code = serializers.CharField(source="sku.sku_code", read_only=True)

    class Meta:
        model = HubInventory
        fields = ["id","hub","hub_code","sku","sku_code","qty"]

class InventoryAdjustSerializer(serializers.Serializer):
    hub = serializers.PrimaryKeyRelatedField(queryset=Hub.objects.all())
    sku = serializers.PrimaryKeyRelatedField(queryset=SKU.objects.all())
    direction = serializers.ChoiceField(choices=[("IN","IN"),("OUT","OUT")])
    qty = serializers.IntegerField(min_value=1)
    note = serializers.CharField(max_length=240, required=False, allow_blank=True)
