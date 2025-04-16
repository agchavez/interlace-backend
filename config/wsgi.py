import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')


from django.conf import settings

print(settings.DEFAULT_FILE_STORAGE,  "settings.DEFAULT_FILE_STORAGE wsgi.py")

application = get_wsgi_application()
