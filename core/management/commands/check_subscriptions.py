from django.core.management.base import BaseCommand
from core.models import UserSubscription

class Command(BaseCommand):
    help = 'Vérifie les abonnements expirés'

    def handle(self, *args, **options):
        count = UserSubscription.check_expired()
        self.stdout.write(f"{count} abonnements désactivés")