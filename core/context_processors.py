from .models import UserSubscription
def subscription_context(request):
    context = {}
    if request.user.is_authenticated:
        try:
            subscription = UserSubscription.objects.get(user=request.user)
            context['has_active_subscription'] = subscription.is_subscribed()
            context['user_subscription'] = subscription
        except UserSubscription.DoesNotExist:
            context['has_active_subscription'] = False
    return context