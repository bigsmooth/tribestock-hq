from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Hub(models.Model):
    name = models.CharField(max_length=120)
    code = models.CharField(max_length=20, unique=True)
    city = models.CharField(max_length=120, blank=True)
    country = models.CharField(max_length=120, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.code} – {self.name}"

class SKU(models.Model):
    name = models.CharField(max_length=180)
    sku_code = models.CharField(max_length=64, unique=True)
    color = models.CharField(max_length=80, blank=True)
    size = models.CharField(max_length=40, blank=True)
    barcode = models.CharField(max_length=64, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.sku_code} – {self.name}"

class Inventory(models.Model):
    hub = models.ForeignKey("Hub", on_delete=models.CASCADE, related_name="inventory")
    sku = models.ForeignKey("SKU", on_delete=models.CASCADE, related_name="inventory")
    quantity = models.IntegerField(default=0)
    class Meta:
        constraints = [models.UniqueConstraint(fields=["hub", "sku"], name="uniq_hub_sku")]
    def __str__(self):
        return f"{self.hub.code}:{self.sku.sku_code} = {self.quantity}"

class InventoryLog(models.Model):
    IN, OUT = "IN", "OUT"
    DIR_CHOICES = [(IN, "In"), (OUT, "Out")]
    hub = models.ForeignKey(Hub, on_delete=models.CASCADE)
    sku = models.ForeignKey(SKU, on_delete=models.CASCADE)
    direction = models.CharField(max_length=3, choices=DIR_CHOICES)
    delta = models.IntegerField()
    before_qty = models.IntegerField()
    after_qty = models.IntegerField()
    note = models.CharField(max_length=240, blank=True)
    actor = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["-created_at"]
    def __str__(self):
        sign = "+" if self.direction == self.IN else "-"
        return f"{self.created_at:%Y-%m-%d %H:%M} {self.hub.code} {self.sku.sku_code} {sign}{self.delta} -> {self.after_qty}"
