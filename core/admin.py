from django.contrib import admin
from .models import Hub, SKU, Inventory, InventoryLog

@admin.register(Hub)
class HubAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "city", "country", "active", "created_at")
    list_filter = ("active", "city", "country")
    search_fields = ("code", "name", "city", "country")
    ordering = ("code",)

@admin.register(SKU)
class SKUAdmin(admin.ModelAdmin):
    list_display = ("sku_code", "name", "color", "size", "active", "created_at")
    list_filter = ("active", "color", "size")
    search_fields = ("sku_code", "name", "barcode", "color", "size")
    ordering = ("sku_code",)

@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ("hub", "sku", "quantity")
    list_filter = ("hub",)
    search_fields = ("hub__code", "sku__sku_code", "sku__name")

@admin.register(InventoryLog)
class InventoryLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "hub", "sku", "direction", "delta", "before_qty", "after_qty", "actor")
    list_filter = ("hub", "direction", "actor")
    search_fields = ("hub__code", "sku__sku_code", "sku__name", "note")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
