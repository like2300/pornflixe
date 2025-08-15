from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings

class MediaStorage(S3Boto3Storage):
    location = 'media'
    file_overwrite = False
    default_acl = 'public-read'
    custom_domain = settings.AWS_S3_CUSTOM_DOMAIN

class StaticStorage(S3Boto3Storage):
    location = 'static'
    file_overwrite = False
    default_acl = 'public-read'
    custom_domain = settings.AWS_S3_CUSTOM_DOMAIN
    object_parameters = {
        'CacheControl': 'max-age=31536000',  # 1 an de cache
    }