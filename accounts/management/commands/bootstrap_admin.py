import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    """
    Non-interactive admin creation for hosts without shell access
    (e.g. Render's free tier). Reads credentials from environment
    variables and only creates the account if it doesn't already
    exist, so it is safe to run on every deploy.

    Set these env vars on Render, then redeploy:
      ADMIN_USERNAME
      ADMIN_EMAIL
      ADMIN_PASSWORD
    """

    help = "Create the first Administrator from ADMIN_USERNAME/ADMIN_EMAIL/ADMIN_PASSWORD env vars, if not already present."

    def handle(self, *args, **options):
        username = os.environ.get("ADMIN_USERNAME")
        email = os.environ.get("ADMIN_EMAIL", "")
        password = os.environ.get("ADMIN_PASSWORD")

        if not username or not password:
            self.stdout.write(self.style.WARNING(
                "ADMIN_USERNAME / ADMIN_PASSWORD not set - skipping admin bootstrap."
            ))
            return

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.SUCCESS(
                f"Administrator '{username}' already exists - skipping."
            ))
            return

        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            role=User.Role.ADMIN,
        )
        user.must_change_password = False
        user.save()
        self.stdout.write(self.style.SUCCESS(f"Administrator '{username}' created successfully."))
