from django.contrib import admin
from apps.user.models import UserModel, DetailGroup
from django.contrib.auth.models import Permission, ContentType

# Register your models here.
admin.site.register(UserModel)
admin.site.register(Permission)
admin.site.register(ContentType)
admin.site.register(DetailGroup)

admin.site.site_header = 'Panel de administración de la aplicación'
admin.site.site_title = 'Panel de administración de la aplicación'
admin.site.index_title = 'Panel de administración de la aplicación'
admin.site.site_url = None

# tema claro
# admin.site.index_template = 'admin/index.html'