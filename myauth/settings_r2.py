from .settings import *  # Importe les paramètres de base

print("🔧 Using simplified R2 settings file")

# === R2 Storage Configuration ===
# Force l'utilisation des classes de stockage R2
DEFAULT_FILE_STORAGE = 'core.storage.MediaStorage'
STATICFILES_STORAGE = 'core.storage.StaticStorage'

# === Configuration S3/R2 ===
# Assurez-vous que ces variables sont bien dans votre .env
AWS_ACCESS_KEY_ID = config('R2_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = config('R2_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = config('R2_BUCKET_NAME')
AWS_S3_ENDPOINT_URL = config('R2_ENDPOINT_URL')
AWS_S3_CUSTOM_DOMAIN = config('R2_CDN_DOMAIN', default='').replace('https://', '')

# === Paramètres spécifiques à R2 ===
AWS_S3_REGION_NAME = 'auto'
AWS_DEFAULT_ACL = 'public-read'
AWS_QUERYSTRING_AUTH = False
AWS_S3_FILE_OVERWRITE = False
AWS_S3_ADDRESSING_STYLE = 'virtual'
AWS_S3_SIGNATURE_VERSION = 's3v4'
AWS_S3_SECURE_URLS = True
AWS_S3_USE_SSL = True

# === URLs pour les fichiers ===
if AWS_S3_CUSTOM_DOMAIN:
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'
    STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'
else:
    # Fallback si le domaine CDN n'est pas défini
    MEDIA_URL = f'{AWS_S3_ENDPOINT_URL}/{AWS_STORAGE_BUCKET_NAME}/media/'
    STATIC_URL = f'{AWS_S3_ENDPOINT_URL}/{AWS_STORAGE_BUCKET_NAME}/static/'

print(f"STATICFILES_STORAGE set to: {STATICFILES_STORAGE}")