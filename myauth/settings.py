 
from pathlib import Path
import os
from decouple import config, Csv

# === BASE DIRECTORIES ===
BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')

# === SECURITY ===
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS =  ['*']
SITE_ID = 1

 

# === APPLICATIONS ===
INSTALLED_APPS = [
    # UI theme
    'unfold', 
    # Django core
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',

    # Local apps
    'core.apps.CoreConfig',

    # Third-party
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'widget_tweaks',

    # paypal
    'paypal.standard.ipn'
]

 
# === MIDDLEWARE ===
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'core.middleware.SubscriptionMiddleware', 
]

# Utilisez des workers asynchrones
# Dans settings.py
FILE_UPLOAD_HANDLERS = [
    'django.core.files.uploadhandler.TemporaryFileUploadHandler',
]

# === URLS & WSGI ===
ROOT_URLCONF = 'myauth.urls'

WSGI_APPLICATION = "myauth.wsgi.application"
# === TEMPLATES ===
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [TEMPLATES_DIR],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.subscription_context',
            ],
        },
    },
]

# === AUTHENTICATION BACKENDS ===
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]
# settings.py
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

 
# === DJANGO ALLAUTH SETTINGS ===  
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
ACCOUNT_UNIQUE_EMAIL = True 
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
LOGIN_REDIRECT_URL = '/home'
ACCOUNT_LOGOUT_REDIRECT_URL = '/accounts/login/'
ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'https' if not DEBUG else 'http'
 

# === EMAIL CONFIG ===
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=not DEBUG, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='webmaster@localhost')

# === DATABASE ===
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# === STATIC & MEDIA FILES ===
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# === SECURITY (Production) ===
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default='http://localhost:8000,http://127.0.0.1:8000',
    cast=Csv()
)


# settings.py (en production)
 

# === Cloudflare R2 === 
# === Cloudflare R2 Configuration ===
if not DEBUG:
    # Configuration de base
    AWS_ACCESS_KEY_ID = config('R2_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = config('R2_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = config('R2_BUCKET_NAME')
    AWS_S3_ENDPOINT_URL = config('R2_ENDPOINT_URL')  # Format: https://<account-id>.r2.cloudflarestorage.com
    AWS_S3_CUSTOM_DOMAIN = config('R2_CDN_DOMAIN').replace('https://', '')  # Retire le https:// du domaine
    
    # Paramètres critiques
    AWS_S3_REGION_NAME = 'auto'
    AWS_DEFAULT_ACL = 'public-read'
    AWS_QUERYSTRING_AUTH = False
    AWS_S3_FILE_OVERWRITE = False
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=31536000',  # Cache de 1 an
    }

    # Configuration du stockage
    DEFAULT_FILE_STORAGE = 'core.storage.MediaStorage'
    STATICFILES_STORAGE = 'core.storage.StaticStorage'
    
    # URLs finales - IMPORTANT: format correct sans double https://
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'
    STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'
    
    # Désactive WhiteNoise en production
    MIDDLEWARE.remove('whitenoise.middleware.WhiteNoiseMiddleware')
    
    # Force HTTPS pour les assets
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
else:
    # Configuration de développement
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'


if DEBUG:
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
    MEDIA_URL = '/media/'
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


PAYPAL_CLIENT_ID = config('PAYPAL_CLIENT_ID')
PAYPAL_SECRET = config('PAYPAL_SECRET')             
 
PAYPAL_ENV = config('PAYPAL_ENV', default='sandbox')  # Par défaut sandbox
PAYPAL_TEST = config('PAYPAL_TEST', default=True, cast=bool)                 # False en prod
PAYPAL_RECEIVER_EMAIL =  config('PAYPAL_RECEIVER_EMAIL', default='sb-chiak44231938@business.example.com')
SUPPORT_EMAIL = "support@tonsite.com"
# === SOCIAL LOGIN (GOOGLE) ===

# === SOCIAL LOGIN (GOOGLE) ===

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {
            'access_type': 'online',
            'prompt': 'select_account'
        },
        'OAUTH_PKCE_ENABLED': True,  # Recommandé pour la sécurité
        'APP': {
            'client_id': config('CLIENT_ID'),  # Renommez pour plus de clarté
            'secret': config('CLIENT_SECRET'),
            'key': ''
        }
    }
}


# Configuration Allauth supplémentaire
ACCOUNT_EMAIL_REQUIRED = True
SOCIALACCOUNT_EMAIL_REQUIRED = True
SOCIALACCOUNT_QUERY_EMAIL = True
SOCIALACCOUNT_STORE_TOKENS = True


SOCIALACCOUNT_ADAPTER = 'core.adapters.CustomSocialAccountAdapter'



LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
        'allauth': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'core': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
        },
    },
}


import logging
logger = logging.getLogger(__name__)

def google_login(request):
    logger.info("Tentative de connexion Google initiée")
    # Votre code existant