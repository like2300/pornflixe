from storages.backends.s3boto3 import S3Boto3Storage

class StaticStorage(S3Boto3Storage):
    """
    Stockage pour les fichiers statiques sur R2.
    Définit le dossier de destination et les en-têtes de cache.
    Toutes les autres configurations (bucket, clés, domaine) sont héritées de settings.py.
    """
    location = 'static'
    default_acl = 'public-read'
    object_parameters = {
        'CacheControl': 'max-age=31536000',  # Cache pour 1 an
    }

class MediaStorage(S3Boto3Storage):
    """
    Stockage pour les fichiers médias sur R2.
    Définit le dossier de destination.
    Toutes les autres configurations (bucket, clés, domaine) sont héritées de settings.py.
    """
    location = 'media'
    default_acl = 'public-read'
    file_overwrite = False