from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings

class MediaStorage(S3Boto3Storage):
    location = 'media'
    file_overwrite = False
    default_acl = 'public-read'
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    endpoint_url = settings.AWS_S3_ENDPOINT_URL
    custom_domain = settings.AWS_S3_CUSTOM_DOMAIN
    # Ajout de paramètres pour R2
    secure_urls = True
    querystring_auth = False
    # Assurer l'accès public
    object_parameters = {
        'ACL': 'public-read',
    }

class StaticStorage(S3Boto3Storage):
    location = 'static'
    file_overwrite = False
    default_acl = 'public-read'
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    endpoint_url = settings.AWS_S3_ENDPOINT_URL
    custom_domain = settings.AWS_S3_CUSTOM_DOMAIN
    # Ajout de paramètres pour R2
    secure_urls = True
    querystring_auth = False
    object_parameters = {
        'ACL': 'public-read',
        'CacheControl': 'max-age=31536000',  # 1 an de cache
    }