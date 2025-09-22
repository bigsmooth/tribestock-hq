# core/management/commands/seed_demo.py
from django.core.management.base import BaseCommand, CommandError
from django.apps import apps
from django.db import transaction

HUBS = [("HUB1","Hub 1"), ("HUB2","Hub 2"), ("HUB3","Hub 3"), ("RETAIL","Retail Store")]
SKUS = [
    ("AAA-STRIPES","All American Stripes"),
    ("CAR-WHT-STR","Carolina Blue and White Stripes"),
    ("BLK-HPNK-STR","Black and Hot Pink Stripes"),
    ("JUICY-PURP","Juicy Purple"),
    ("WITCHY","Witchy Vibes"),
]

APP_LABELS = ("core","inventory")

def get_model(name):
    for app in APP_LABELS:
        try:
            return apps.get_model(app, name)
        except LookupError:
            pass
    return None

def fields(m): return {f.name for f in m._meta.get_fields()}

class Command(BaseCommand):
    help = "Seed hubs, SKUs, and inventory (idempotent; handles sku_code/code)."

    @transaction.atomic
    def handle(self, *args, **kwargs):
        Hub = get_model("Hub")
        SKU = get_model("SKU")
        if not Hub or not SKU:
            raise CommandError("Missing Hub or SKU model.")

        Inventory = get_model("Inventory") or get_model("Stock") or get_model("InventoryItem") or get_model("InventoryRecord")

        hub_f = fields(Hub)
        sku_f = fields(SKU)
        inv_f = fields(Inventory) if Inventory else set()

        # ---- Hubs (prefer code if present) ----
        hubs_out = []
        hub_code_field = "code" if "code" in hub_f else ("hub_code" if "hub_code" in hub_f else None)
        for code, name in HUBS:
            if hub_code_field:
                q = {f"{hub_code_field}__iexact": code}
                hub = Hub.objects.filter(**q).first()
                if not hub:
                    # try by name, then set code
                    hub = Hub.objects.filter(name=name).first() if "name" in hub_f else None
                    if hub:
                        setattr(hub, hub_code_field, code)
                        if "name" in hub_f and getattr(hub,"name",None)!=name: hub.name = name
                        hub.save()
                    else:
                        data = {hub_code_field: code}
                        if "name" in hub_f: data["name"] = name
                        hub = Hub.objects.create(**data)
                else:
                    if "name" in hub_f and getattr(hub,"name",None)!=name:
                        hub.name = name; hub.save()
            else:
                hub, _ = Hub.objects.get_or_create(**({"name": name} if "name" in hub_f else {}))
            hubs_out.append(hub)
        self.stdout.write(self.style.SUCCESS(f"Hubs ensured: {', '.join([getattr(h,'name',str(h.pk)) for h in hubs_out])}"))

        # ---- SKUs (handle sku_code/code + existing blanks) ----
        sku_code_field = "sku_code" if "sku_code" in sku_f else ("code" if "code" in sku_f else None)
        sku_name_field = "name" if "name" in sku_f else ("product_name" if "product_name" in sku_f else None)

        for code, name in SKUS:
            sku = None
            if sku_code_field:
                sku = SKU.objects.filter(**{f"{sku_code_field}__iexact": code}).first()
            if not sku and sku_name_field:
                sku = SKU.objects.filter(**{sku_name_field: name}).first()
            if sku:
                # Update missing/wrong code or name
                if sku_code_field and (not getattr(sku, sku_code_field, "") or getattr(sku, sku_code_field) != code):
                    setattr(sku, sku_code_field, code)
                if sku_name_field and getattr(sku, sku_name_field, None) != name:
                    setattr(sku, sku_name_field, name)
                sku.save()
            else:
                data = {}
                if sku_code_field: data[sku_code_field] = code
                if sku_name_field: data[sku_name_field] = name
                SKU.objects.create(**data)
        self.stdout.write(self.style.SUCCESS("SKUs ensured."))

        # ---- Inventory (optional) ----
        if Inventory:
            hub_fk = "hub" if "hub" in inv_f else None
            sku_fk = "sku" if "sku" in inv_f else None
            qty_field = next((f for f in ["quantity","qty","count","on_hand","stock"] if f in inv_f), None)
            if not (hub_fk and sku_fk):
                self.stdout.write(self.style.WARNING("Inventory model missing hub/sku FKs; skipping."))
                return
            created = 0
            all_skus = list(SKU.objects.all())
            for hub in hubs_out:
                for sku in all_skus:
                    defaults = {qty_field: 0} if qty_field else {}
                    _, was_created = Inventory.objects.get_or_create(**{hub_fk: hub, sku_fk: sku}, defaults=defaults)
                    created += int(was_created)
            self.stdout.write(self.style.SUCCESS(f"Inventory rows ensured ({created} created)."))
        else:
            self.stdout.write(self.style.WARNING("No Inventory-like model found; skipped inventory rows."))
