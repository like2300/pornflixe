from storages.backends.s3boto3 import S3Boto3Storage

class StaticStorage(S3Boto3Storage):
    """
    Stockage personnalisé pour les fichiers statiques, servis depuis le dossier 'static/' de R2.
    Inclut un en-tête de cache de longue durée pour de meilleures performances.
    """
    location = 'static'
    default_acl = 'public-read'
    object_parameters = {
        'CacheControl': 'max-age=31536000',  # Cache pour 1 an
    }

class MediaStorage(S3Boto3Storage):
    """
    Stockage personnalisé pour les fichiers médias téléversés par les utilisateurs,
    servis depuis le dossier 'media/' de R2.
    Assure que les fichiers sont lisibles publiquement et ne sont pas écrasés.
    """
    location = 'media'
    default_acl = 'public-read'
    file_overwrite = False