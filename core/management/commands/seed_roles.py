from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, User

GROUPS = ["Admin", "HubManager", "Retail"]

class Command(BaseCommand):
    help = "Create default groups and optionally add a user to Admin."

    def add_arguments(self, parser):
        parser.add_argument("--user", help="Username to add to Admin", default=None)

    def handle(self, *args, **opts):
        for g in GROUPS:
            Group.objects.get_or_create(name=g)
        self.stdout.write(self.style.SUCCESS(f"Groups ensured: {', '.join(GROUPS)}"))
        if opts["user"]:
            try:
                u = User.objects.get(username=opts["user"])
                admin = Group.objects.get(name="Admin")
                u.groups.add(admin)
                self.stdout.write(self.style.SUCCESS(f"Added {u.username} to Admin"))
            except User.DoesNotExist:
                self.stderr.write(f"User {opts['user']} not found")
