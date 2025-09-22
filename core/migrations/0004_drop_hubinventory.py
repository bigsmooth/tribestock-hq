from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ("core", "0003_copy_hubinv_to_inventory"),
    ]
    operations = [
        migrations.DeleteModel(name="HubInventory"),
    ]
