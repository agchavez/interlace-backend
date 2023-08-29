
# Rest_framework
from rest_framework import mixins, viewsets, permissions
from rest_framework.decorators import permission_classes, action
from rest_framework.permissions import IsAuthenticated, IsAdminUser, IsAuthenticatedOrReadOnly, BasePermission
from rest_framework.response import Response

# Models
from apps.user.models import UserModel
from django.contrib.auth.models import Group, Permission

from django.contrib.auth import get_user_model
User = get_user_model()

# Log de administrador
from django.contrib.admin.models import LogEntry

# Serializers
from apps.user.serializers import (UserSerializer,
                                   LogEntrySerializer)

# filters
from django_filters.rest_framework import DjangoFilterBackend
import django_filters
from rest_framework.filters import SearchFilter, OrderingFilter


class CustomAccessPermission(BasePermission):
    """
    Clase personalizada de permisos que verifica si el usuario tiene los permisos adecuados.
    """

    def has_permission(self, request, view):
        # usuario esta activo
        if not request.user.is_active:
            return False
        if request.method in permissions.SAFE_METHODS:
            # Si el método es seguro (GET, HEAD, OPTIONS), permitir el acceso a todos
            return True

        # Obtener los permisos requeridos para la acción específica (crear, actualizar, eliminar, etc.)
        required_permissions = view.get_required_permissions(request.method)

        # Verificar si el usuario tiene todos los permisos requeridos
        return request.user.has_perms(required_permissions)



# ViewSets by UserModel
class UserViewSet(mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin,
                  mixins.DestroyModelMixin,
                  mixins.ListModelMixin,
                  viewsets.GenericViewSet):
    queryset = UserModel.objects.all()
    serializer_class = UserSerializer
    filter_backends = (SearchFilter, OrderingFilter)
    search_fields = ('username', 'email', 'first_name', 'last_name')

    # Mapeo de métodos HTTP a los permisos requeridos
    PERMISSION_MAPPING = {
        'GET': ['view_usermodel'],
        'POST': ['add_usermodel'],
        'PUT': ['change_usermodel'],
        'PATCH': ['change_usermodel'],
        'DELETE': ['delete_usermodel']
    }

    def get_required_permissions(self, http_method):
        return self.PERMISSION_MAPPING.get(http_method, [])

    # actualizar mi perfil
    @action(methods=['put'], detail=False, permission_classes=[IsAuthenticated], url_path='update-profile')
    def update_profile(self, request):
        user = request.user
        serializer = UserSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)





# Filter by log
class LogEntryFilter(django_filters.FilterSet):
    user = django_filters.ModelMultipleChoiceFilter(
        field_name='user__username',
        to_field_name='username',
        queryset=User.objects.all()

    )
    content_type = django_filters.CharFilter(field_name='content_type__model', lookup_expr='icontains')
    change_message = django_filters.CharFilter(field_name='change_message', lookup_expr='icontains')

    class Meta:
        model = LogEntry
        fields = ['user', 'content_type', 'action_flag', 'change_message']


# ViewSets by LogEntry
@permission_classes([IsAdminUser])
class LogEntryViewSet(mixins.RetrieveModelMixin,
                      mixins.UpdateModelMixin,
                      mixins.ListModelMixin,
                      viewsets.GenericViewSet):
    queryset = LogEntry.objects.all()
    serializer_class = LogEntrySerializer
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_class = LogEntryFilter
    search_fields = ('user__username', 'content_type__model', 'action_flag', 'change_message')
    ordering_fields = ('user__username', 'content_type__model', 'action_flag', 'change_message')