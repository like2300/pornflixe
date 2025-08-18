from storages.backends.s3boto3 import S3Boto3Storage
from botocore.client import Config

class R2Storage(S3Boto3Storage):
    """
    Classe de base pour le stockage sur Cloudflare R2.
    Cette classe force la configuration recommandée par R2 ('virtual addressing').
    """
    # Force la configuration S3 pour être compatible avec R2
    config = Config(s3={'addressing_style': 'virtual'})

class StaticStorage(R2Storage):
    """Stockage pour les fichiers statiques sur R2."""
    location = 'static'
    default_acl = 'public-read'
    object_parameters = {
        'CacheControl': 'max-age=31536000',  # Cache pour 1 an
    }

class MediaStorage(R2Storage):
    """Stockage pour les fichiers médias sur R2."""
    location = 'media'
    default_acl = 'public-read'
    file_overwrite = False
