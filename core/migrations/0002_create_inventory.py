from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Inventory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("quantity", models.IntegerField(default=0)),
                ("hub", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="inventory", to="core.hub")),
                ("sku", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="inventory", to="core.sku")),
            ],
        ),
        migrations.AddConstraint(
            model_name="inventory",
            constraint=models.UniqueConstraint(fields=("hub", "sku"), name="uniq_hub_sku"),
        ),
    ]
