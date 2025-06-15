from django.contrib.auth import get_user_model
from .models import UserSubscription

def subscription_context(request):
    context = {}
    if hasattr(request, 'has_active_subscription'):  # Utilise les valeurs du middleware
        context['has_active_subscription'] = request.has_active_subscription
        context['user_subscription'] = getattr(request, 'user_subscription', None)
    elif request.user.is_authenticated:
        try:
            subscription = UserSubscription.objects.get(user=request.user)
            context['has_active_subscription'] = subscription.is_subscribed()
            context['user_subscription'] = subscription
        except UserSubscription.DoesNotExist:
            context['has_active_subscription'] = False
    return context