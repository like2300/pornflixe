from django.utils import timezone
from .models import UserSubscription

def paypal_config(request):
    from django.conf import settings
    return {
        'PAYPAL_TEST': settings.PAYPAL_TEST,
        'PAYPAL_CLIENT_ID': settings.PAYPAL_CLIENT_ID,
    }

def subscription_context(request):
    context = {
        'has_active_subscription': False,
        'user_subscription': None
    }
    
    if request.user.is_authenticated:
        try:
            # Utilisation de getattr pour éviter DoesNotExist si le related_name est différent
            subscription = getattr(request.user, 'subscription', None)
            
            if subscription:
                # Version 1: Utilisation directe des champs (recommandé)
                context['has_active_subscription'] = (
                    subscription.is_active and 
                    subscription.end_date > timezone.now()
                )
                
                # Version alternative: Utilisation de la property is_subscribed
                # context['has_active_subscription'] = subscription.is_subscribed
                
                context['user_subscription'] = subscription
                
        except Exception as e:
            # Log l'erreur mais ne casse pas le template
            from django.utils.log import logger
            logger.error(f"Error checking subscription: {str(e)}")
    
    return context