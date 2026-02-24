from django.contrib import admin
from apps.user.models import UserModel, DetailGroup, PushSubscription
from django.contrib.auth.models import Permission, ContentType


@admin.register(PushSubscription)
class PushSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'endpoint_short', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['user__username', 'user__email', 'endpoint']
    readonly_fields = ['endpoint', 'auth', 'p256dh', 'created_at', 'updated_at']

    def endpoint_short(self, obj):
        return f"{obj.endpoint[:50]}..."
    endpoint_short.short_description = 'Endpoint'


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