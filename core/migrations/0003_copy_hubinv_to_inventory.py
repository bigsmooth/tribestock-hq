from django.db import migrations

def forwards(apps, schema_editor):
    HubInventory = apps.get_model("core", "HubInventory")
    Inventory = apps.get_model("core", "Inventory")
    db = schema_editor.connection.alias
    for r in HubInventory.objects.using(db).all():
        inv, created = Inventory.objects.using(db).get_or_create(
            hub_id=r.hub_id,
            sku_id=r.sku_id,
            defaults={"quantity": r.qty or 0},
        )
        if not created:
            inv.quantity = (inv.quantity or 0) + (r.qty or 0)
            inv.save()

class Migration(migrations.Migration):
    dependencies = [
        ("core", "0002_create_inventory"),
    ]
    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
