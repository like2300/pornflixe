from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage

class StaticStorage(S3Boto3Storage):
    """
    Stockage pour les fichiers statiques.
    Les fichiers sont mis en cache pour une longue durée.
    """
    location = 'static'
    default_acl = 'public-read'
    object_parameters = {
        'CacheControl': 'max-age=31536000', # 1 an
    }
    # Utilise le domaine CDN pour générer les URLs
    custom_domain = settings.AWS_S3_CUSTOM_DOMAIN

class MediaStorage(S3Boto3Storage):
    """
    Stockage pour les fichiers médias.
    Les fichiers ne sont pas écrasés et sont publics.
    """
    location = 'media'
    default_acl = 'public-read'
    file_overwrite = False
    # Utilise le domaine CDN pour générer les URLs
    custom_domain = settings.AWS_S3_CUSTOM_DOMAIN
