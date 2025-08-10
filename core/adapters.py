# core/adapters.py
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialApp
from django.core.exceptions import MultipleObjectsReturned, ImproperlyConfigured
import logging

logger = logging.getLogger(__name__)

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def get_app(self, request, provider, **kwargs):
        try:
            if kwargs.get('client_id'):
                return SocialApp.objects.get(
                    provider=provider,
                    client_id=kwargs['client_id']
                )
            return super().get_app(request, provider)
        except MultipleObjectsReturned:
            logger.warning(f"Multiple SocialApp entries for {provider}")
            return SocialApp.objects.filter(provider=provider).first()
        except SocialApp.DoesNotExist as e:
            logger.error(f"SocialApp not found: {str(e)}")
            raise ImproperlyConfigured(
                f"Configuration {provider} manquante. Vérifiez l'admin Django."
            ) from e