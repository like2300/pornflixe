import logging
from datetime import timedelta
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings
from .models import UserSubscription

logger = logging.getLogger(__name__)

def check_expired_subscriptions():
    """Vérifie les abonnements expirés"""
    today = timezone.now().date()
    logger.info(f"Checking expired subscriptions for {today}")
    
    expired_subs = UserSubscription.objects.filter(
        end_date__lt=today,
        is_active=True
    ).select_related('user')

    for sub in expired_subs:
        try:
            # Envoi email
            send_expiration_notification(sub)
            
            # Désactive l'abonnement
            sub.is_active = False
            sub.save()
            
            logger.info(f"Disabled expired subscription for {sub.user.email}")
            
        except Exception as e:
            logger.error(f"Error processing subscription {sub.id}: {str(e)}")

def send_expiration_notification(subscription):
    """Envoie la notification d'expiration"""
    context = {
        'user': subscription.user,
        'end_date': subscription.end_date,
        'site_name': settings.SITE_NAME,
        'renewal_url': f"{settings.SITE_URL}/renew/"
    }
    
    subject = f"{settings.SITE_NAME} - Abonnement expiré"
    email = EmailMultiAlternatives(
        subject,
        render_to_string('emails/subscription_expired.txt', context),
        settings.DEFAULT_FROM_EMAIL,
        [subscription.user.email]
    )
    email.attach_alternative(
        render_to_string('emails/subscription_expired.html', context),
        "text/html"
    )
    email.send()

def daily_subscription_check():
    """Point d'entrée principal pour le cron job"""
    logger.info("=== Starting daily subscription check ===")
    check_expired_subscriptions()
    logger.info("=== Daily check completed ===")