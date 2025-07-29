from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from django.conf import settings
from django.db.models import F, Count, Prefetch
from django.db import transaction
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from datetime import timedelta
import logging                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  

logger = logging.getLogger(__name__)

class SubscriptionMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.has_active_subscription = False
        if request.user.is_authenticated:
            try:
                request.has_active_subscription = (
                    hasattr(request.user, 'subscription') and 
                    request.user.subscription.is_subscribed
                )
            except Exception as e:
                logger.error(f"Subscription middleware error: {str(e)}")


class PayPalDebugMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if 'paypal' in request.path:
            from django.conf import settings
            import pprint
            logger = logging.getLogger('paypal')
            logger.debug(f"PayPal Request:\n{pprint.pformat(request.POST)}")
        return self.get_response(request)