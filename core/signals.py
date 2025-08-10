from allauth.account.signals import email_confirmed
from django.dispatch import receiver

@receiver(email_confirmed)
def auto_login_after_email_confirm(request, email_address, **kwargs):
    # Force la connexion après confirmation d'email
    user = email_address.user
    user.backend = 'django.contrib.auth.backends.ModelBackend'
    from django.contrib.auth import login
    login(request, user)

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import UserSubscription
from datetime import timedelta

@receiver(post_save, sender=UserSubscription)
def set_subscription_dates(sender, instance, created, **kwargs):
    """Définit automatiquement la date de fin"""
    if created and instance.plan:
        instance.end_date = timezone.now() + timedelta(days=instance.plan.duration_days)
        instance.save()