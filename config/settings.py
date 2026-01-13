import os
from pathlib import Path
from datetime import timedelta
from decouple import config

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY')

DEBUG = config('DEBUG', default=False, cast=bool)
APPEND_SLASH = False

ALLOWED_HOSTS = ['*']

# cors
CORS_ALLOWED_ALL_ORIGINS = True
CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True

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

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
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
    )
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

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'



CORS_EXPOSE_HEADERS = ['Content-Disposition']

# Configuracion celery

CELERY_BROKER_URL = config('CELERY_BROKER_REDIS_URL', default='redis://localhost:6379')
CELERY_RESULT_BACKEND = "django-db"
CELERY_RESULT_EXPIRES = 86400  # Tiempo en segundos (un día)



CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers.DatabaseScheduler'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Configuracion de canales
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("localhost", 6379)],
        },
    },
}
#sp=racwdli&st=2025-03-19T15:09:16Z&se=2025-12-06T23:09:16Z&sip=181.115.60.7&sv=2022-11-02&sr=c&sig=***REMOVED***
#https://trackerlogisticstorage.blob.core.windows.net/tracker?sp=racwdli&st=2025-03-19T15:09:16Z&se=2025-12-06T23:09:16Z&sip=181.115.60.7&sv=2022-11-02&sr=c&sig=***REMOVED***
AZURE_ACCOUNT_NAME = "trackerlogisticstorage"
AZURE_ACCOUNT_KEY = "***REMOVED***"
AZURE_CONTAINER = "tracker"
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
            'custom_domain': AZURE_CUSTOM_DOMAIN,
        },
    },
   "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    }
}
