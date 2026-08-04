import getpass

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

User = get_user_model()


class Command(BaseCommand):
    help = "Create the first Administrator account from the terminal (like createsuperuser)."

    def add_arguments(self, parser):
        parser.add_argument("--username", help="Administrator username")
        parser.add_argument("--email", help="Administrator email")

    def handle(self, *args, **options):
        username = options.get("username") or input("Username: ")
        if User.objects.filter(username=username).exists():
            raise CommandError(f"User '{username}' already exists.")

        email = options.get("email") or input("Email: ")

        password = getpass.getpass("Password: ")
        password_confirm = getpass.getpass("Password (again): ")
        if password != password_confirm:
            raise CommandError("Passwords did not match.")
        if len(password) < 8:
            raise CommandError("Password must be at least 8 characters long.")

        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            role=User.Role.ADMIN,
        )
        user.must_change_password = False
        user.save()
        self.stdout.write(self.style.SUCCESS(f"Administrator '{username}' created successfully."))
