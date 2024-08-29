from argparse import ArgumentParser

from django.core.management import BaseCommand

from accounts.models import Account


class Command(BaseCommand):
    help = "Create service user (ex. for telegram bot)"

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument("email", type=str)
        parser.add_argument("password", type=str)

    def handle(self, email: str, password: str, *args, **kwargs) -> None:
        if Account.objects.filter(email=email).exists():
            self.stderr.write(self.style.ERROR(f"User `{email}` already exists"))
            return

        user = Account.objects.create_user(
            email=email,
            password=password,
            username=f"service_{email}",
            is_organizator=True,
            is_active=True,
        )
        user.is_admin = True
        user.save()
        self.stdout.write(self.style.SUCCESS(f"Successfully created user: {email}"))
