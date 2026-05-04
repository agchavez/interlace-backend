import os
from pathlib import Path
from datetime import timedelta
from decouple import config

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-bhjfjy4hy_6)c2qv@-yd28b$o&4w0*&%ge*yjy3zk+8svk1b69'

DEBUG = config('DEBUG', default=False, cast=bool)
APPEND_SLASH = False

ALLOWED_HOSTS = ['*']

# cors
CORS_ALLOWED_ALL_ORIGINS = True
CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True
# Headers adicionales permitidos por CORS. Sin esto el browser rechaza
# /api/tv/* porque el header custom X-TV-Token no está en la lista default
# de django-cors-headers.
from corsheaders.defaults import default_headers
CORS_ALLOW_HEADERS = list(default_headers) + ['x-tv-token']

# Application definition
LOCAL_APPS = [
    'apps.user',
    'apps.authentication',
    'apps.maintenance',
    'apps.tracker',
    'apps.report',
    'apps.order',
    'apps.inventory',
    'apps.imported',
    'apps.document',
    'apps.personnel',
    'apps.tokens',
    'apps.truck_cycle',
    'apps.tv',
    'apps.workstation',
    'apps.repack',
]

INSTALLED_APPS = [
                    'daphne',
                     'django.contrib.admin',
                     'django.contrib.auth',
                     'django.contrib.contenttypes',
                     'django.contrib.sessions',
                     'django.contrib.messages',
                     'django.contrib.staticfiles',
                     'rest_framework',
                     'corsheaders',
                     'django_filters',
                     'import_export',
                     'django_celery_beat',
                     'django_celery_results',
                      'channels',
                      'storages',
                 ] + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Servir archivos estáticos en producción
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware'
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),  # Asegúrate de que 'templates' esté incluido aquí
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

ASGI_APPLICATION = 'config.asgi.application'
WSGI_APPLICATION = 'config.wsgi.application'

AUTH_USER_MODEL = 'user.UserModel'

# Custom authentication backend for email-based authentication
AUTHENTICATION_BACKENDS = [
    'apps.authentication.backends.EmailBackend',  # Custom email backend
    'django.contrib.auth.backends.ModelBackend',  # Default backend as fallback
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
        'TEST': {
            'NAME': 'test_tracker_db',
            'TEMPLATE': 'template0',  # Use template0 to avoid collation issues
        }
    }
}

# EMAIL SETTINGS
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS')
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
EMAIL_PORT = os.getenv('EMAIL_PORT')


# REST FRAMEWORK
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 15,
    'EXCEPTION_HANDLER': 'utils.custom_exception_handler',
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ) if not DEBUG else (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),
    'COERCE_DECIMAL_TO_STRING': False,
}

SIMPLE_JWT = {
    "TOKEN_OBTAIN_SERIALIZER": "utils.jwt.MyTokenObtainPairSerializer",
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=120),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": True,
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Configuraciones de localizacion
USE_TZ = True
LANGUAGE_CODE = 'es-HN'

TIME_ZONE = 'America/Tegucigalpa'

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# Directorios de archivos estáticos fuente (se copian a STATIC_ROOT con collectstatic)
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'staticfiles'),
]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'



CORS_EXPOSE_HEADERS = ['Content-Disposition']

# Configuracion celery

CELERY_BROKER_URL = config('CELERY_BROKER_REDIS_URL', default='redis://localhost:6379')
CELERY_RESULT_BACKEND = "django-db"
CELERY_RESULT_EXPIRES = 86400  # Tiempo en segundos (un día)



CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers.DatabaseScheduler'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Configuracion de canales — acepta REDIS_URL (con auth) o REDIS_HOST/PORT.
_REDIS_URL = os.getenv('REDIS_URL', '').strip()
_CHANNEL_HOSTS = (
    [_REDIS_URL]
    if _REDIS_URL
    else [(os.getenv('REDIS_HOST', 'localhost'), int(os.getenv('REDIS_PORT', '6379')))]
)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": _CHANNEL_HOSTS,
        },
    },
}
#sp=racwdli&st=2025-03-19T15:09:16Z&se=2025-12-06T23:09:16Z&sip=181.115.60.7&sv=2022-11-02&sr=c&sig=***REMOVED***
#https://trackerlogisticstorage.blob.core.windows.net/tracker?sp=racwdli&st=2025-03-19T15:09:16Z&se=2025-12-06T23:09:16Z&sip=181.115.60.7&sv=2022-11-02&sr=c&sig=***REMOVED***
AZURE_ACCOUNT_NAME = os.getenv("AZURE_ACCOUNT_NAME", "trackerlogisticstorage")
AZURE_ACCOUNT_KEY = os.getenv("AZURE_ACCOUNT_KEY", "")
AZURE_CONTAINER = os.getenv("AZURE_CONTAINER", "tracker")
AZURE_CUSTOM_DOMAIN = f"{AZURE_ACCOUNT_NAME}.blob.core.windows.net"

#DEFAULT_FILE_STORAGE = "apps.core.storage_backends.AzureMediaStorage"
MEDIA_URL = f"https://{AZURE_CUSTOM_DOMAIN}/{AZURE_CONTAINER}/"

# Configuracion de configuracion de seguridad de azure blob
AZURE_OBJECT_PARAMETERS = {
    "CacheControl": "max-age=86400",

}

STORAGES = {
    'default': {
        'BACKEND': 'storages.backends.azure_storage.AzureStorage',
        'options': {
            'account_name': AZURE_ACCOUNT_NAME,
            'account_key': AZURE_ACCOUNT_KEY,
            'azure_container': AZURE_CONTAINER,
            'expiration_secs': 3600,
        },
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    }
}

# Configuracion de logging
from config.logging_config import LOGGING

# URL del frontend para links en correos electrónicos
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')

# Web Push Notifications - VAPID Configuration
# Llaves VAPID hardcodeadas para simplificar deployment
VAPID_PUBLIC_KEY = 'BHBnNHH1RSyj2e5_zIpdvt4pPgXUCQl4IfMWkrzHYoDoFQMR0qFuYNK7Sh6qbTyZ1xzGGz1G6iQ-35lX8TnhiGw'
VAPID_PRIVATE_KEY = """-----BEGIN PRIVATE KEY-----
MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQgVBAyOFj26joNLLFx
qN4jPz7zvTkHmDCydcpgvarhbs6hRANCAARwZzRx9UUso9nuf8yKXb7eKT4F1AkJ
eCHzFpK8x2KA6BUDEdKhbmDSu0oeqm08mdccxhs9RuokPt+ZV/E54Yhs
-----END PRIVATE KEY-----"""
VAPID_ADMIN_EMAIL = 'tracker.logistics@outlook.com'