from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.trades.models import Account


class Command(BaseCommand):
    help = "Lista los usuarios existentes y sus cuentas de trading."

    def handle(self, *args, **options):
        User = get_user_model()
        users = User.objects.all().order_by("id")
        if not users:
            self.stdout.write(self.style.WARNING("No hay usuarios creados."))
            return

        for user in users:
            self.stdout.write(self.style.SUCCESS(f"\nUsuario #{user.id}: {user.username} <{user.email}>"))
            accounts = Account.objects.filter(user=user)
            if not accounts:
                self.stdout.write("   (sin cuentas)")
            for acc in accounts:
                self.stdout.write(
                    f"   -> Cuenta #{acc.id}: \"{acc.name}\" [{acc.get_account_type_display()}] "
                    f"balance inicial ${acc.initial_balance} | trades actuales: {acc.trades.count()}"
                )