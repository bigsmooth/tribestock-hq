from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group

ROLES = ["Admin", "HubManager", "Retail", "Supplier"]

class Command(BaseCommand):
    help = "Create default groups (roles)"

    def handle(self, *args, **kwargs):
        for name in ROLES:
            Group.objects.get_or_create(name=name)
        self.stdout.write(self.style.SUCCESS(f"Seeded roles: {', '.join(ROLES)}"))
