"""
Vistas para gestión de personal
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q, Count, Avg
from datetime import date, timedelta
from django.contrib.auth import get_user_model

User = get_user_model()

from ..models.personnel import PersonnelProfile, EmergencyContact
from ..models.organization import Area, Department
from ..serializers.personnel_serializers import (
    PersonnelProfileListSerializer,
    PersonnelProfileDetailSerializer,
    PersonnelProfileCreateUpdateSerializer,
    EmergencyContactSerializer,
    AreaSerializer,
    DepartmentSerializer
)
from ..filters import PersonnelProfileFilter
from ..permissions import (
    CanViewPersonnel,
    CanManagePersonnel,
    IsSupervisorOrAbove,
    IsAreaManagerOrAbove,
    IsCDManager
)


class AreaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para Áreas
    """
    queryset = Area.objects.filter(is_active=True)
    serializer_class = AreaSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None  # Sin paginación para catálogos


class DepartmentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para Departamentos
    """
    queryset = Department.objects.filter(is_active=True).select_related('area')
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['area']
    pagination_class = None


class PersonnelProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet completo para perfiles de personal

    list: Listar personal con filtros
    retrieve: Obtener detalle de un perfil
    create: Crear nuevo perfil
    update: Actualizar perfil completo
    partial_update: Actualizar parcialmente
    destroy: Desactivar perfil (soft delete)

    Acciones personalizadas:
    - my_profile: Obtener mi propio perfil
    - dashboard: Dashboard con estadísticas
    - certifications_expiring: Personal con certificaciones por vencer
    - supervised_personnel: Personal que superviso
    - subordinates_tree: Árbol de subordinados
    - performance_summary: Resumen de desempeño
    """
    queryset = PersonnelProfile.objects.select_related(
        'user',
        'area',
        'department',
        'primary_distributor_center',
        'immediate_supervisor'
    ).prefetch_related(
        'emergency_contacts',
        'certifications',
        'medical_records'
    )
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = PersonnelProfileFilter
    search_fields = [
        'employee_code',
        'first_name',
        'last_name',
        'email',
        'position'
    ]
    ordering_fields = [
        'employee_code',
        'first_name',
        'hire_date',
        'hierarchy_level',
        'is_active'
    ]
    ordering = ['-is_active', 'first_name']

    def get_serializer_class(self):
        if self.action == 'list':
            return PersonnelProfileListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return PersonnelProfileCreateUpdateSerializer
        return PersonnelProfileDetailSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), CanManagePersonnel()]
        elif self.action in ['dashboard', 'certifications_expiring']:
            return [IsAuthenticated(), IsSupervisorOrAbove()]
        return [IsAuthenticated(), CanViewPersonnel()]

    def get_queryset(self):
        """
        Filtrar queryset basado en permisos del usuario
        """
        queryset = super().get_queryset()
        user = self.request.user

        # Superusuarios y staff ven todo
        if user.is_superuser or user.is_staff:
            return queryset

        # Usuarios con permiso de Django ven todo
        if user.has_perm('personnel.view_all_personnel') or user.has_perm('personnel.manage_personnel'):
            return queryset

        try:
            user_personnel = user.personnel_profile
        except PersonnelProfile.DoesNotExist:
            return queryset.none()

        # Gerente CD ve todo su centro
        if user_personnel.hierarchy_level == PersonnelProfile.CD_MANAGER:
            return queryset.filter(
                primary_distributor_center=user_personnel.primary_distributor_center
            )

        # Jefe de área ve su área
        if user_personnel.hierarchy_level == PersonnelProfile.AREA_MANAGER:
            return queryset.filter(area=user_personnel.area)

        # Supervisor ve su equipo
        if user_personnel.hierarchy_level == PersonnelProfile.SUPERVISOR:
            subordinates_ids = [p.id for p in user_personnel.get_all_subordinates()]
            return queryset.filter(
                Q(id=user_personnel.id) |
                Q(id__in=subordinates_ids) |
                Q(immediate_supervisor=user_personnel)
            )

        # Operativo solo ve su perfil
        return queryset.filter(id=user_personnel.id)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_destroy(self, instance):
        """Soft delete - marcar como inactivo"""
        instance.is_active = False
        instance.termination_date = date.today()
        instance.save()

    @action(detail=False, methods=['get'])
    def my_profile(self, request):
        """
        Obtener el perfil del usuario autenticado
        GET /api/personnel/profiles/my_profile/
        """
        try:
            profile = request.user.personnel_profile
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        except PersonnelProfile.DoesNotExist:
            return Response(
                {
                    'has_profile': False,
                    'message': 'Debe completar su perfil de personal',
                    'user': {
                        'id': request.user.id,
                        'username': request.user.username,
                        'email': request.user.email,
                        'first_name': request.user.first_name,
                        'last_name': request.user.last_name,
                    }
                },
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def complete_my_profile(self, request):
        """
        Permite a usuarios autenticados sin perfil crear su propio perfil
        POST /api/personnel/profiles/complete_my_profile/

        Body:
        {
            "employee_code": "EMP001",
            "first_name": "Juan",
            "last_name": "Pérez",
            "email": "juan@example.com",
            "primary_distributor_center": 1,
            "area": 1,
            "hierarchy_level": "SUPERVISOR",
            "position": "Supervisor de Turno",
            "position_type": "ADMINISTRATIVE",
            "hire_date": "2024-01-15",
            "contract_type": "PERMANENT",
            "personal_id": "0801-1990-12345",
            "birth_date": "1990-05-20",
            "gender": "M",
            "phone": "+504 9999-9999",
            "address": "Col. Kennedy, Tegucigalpa",
            "city": "Tegucigalpa"
        }
        """
        # Verificar que el usuario NO tenga ya un perfil
        if hasattr(request.user, 'personnel_profile'):
            return Response(
                {
                    'detail': 'Ya tiene un perfil creado',
                    'profile_id': request.user.personnel_profile.id
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Crear el perfil vinculado al usuario autenticado
        serializer = PersonnelProfileCreateUpdateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(
                {
                    'message': 'Perfil creado exitosamente',
                    'profile': serializer.data
                },
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['patch'], permission_classes=[IsAuthenticated])
    def update_my_profile(self, request):
        """
        Permite al usuario actualizar ciertos campos de su propio perfil
        PATCH /api/personnel/profiles/update_my_profile/

        Campos editables por el usuario:
        - email (email personal del trabajo)
        - personal_email (email personal)
        - phone (teléfono)
        - address (dirección)
        - city (ciudad)
        - marital_status (estado civil)
        - shirt_size, pants_size, shoe_size, glove_size, helmet_size (tallas)
        - photo (foto de perfil)

        Campos NO editables (solo por administradores):
        - employee_code, first_name, last_name
        - hierarchy_level, position, position_type
        - area, department, primary_distributor_center, distributor_centers
        - hire_date, contract_type, personal_id, birth_date, gender
        - immediate_supervisor, is_active
        """
        try:
            profile = request.user.personnel_profile
        except PersonnelProfile.DoesNotExist:
            return Response(
                {'detail': 'No tiene un perfil de personal asociado'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Campos permitidos para edición por el usuario
        allowed_fields = [
            'email', 'personal_email', 'phone', 'address', 'city',
            'marital_status', 'shirt_size', 'pants_size', 'shoe_size',
            'glove_size', 'helmet_size', 'photo'
        ]

        # Filtrar solo los campos permitidos
        filtered_data = {
            key: value for key, value in request.data.items()
            if key in allowed_fields
        }

        if not filtered_data:
            return Response(
                {
                    'detail': 'No se proporcionaron campos válidos para actualizar',
                    'allowed_fields': allowed_fields
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Actualizar perfil
        serializer = PersonnelProfileCreateUpdateSerializer(
            profile,
            data=filtered_data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            # Devolver el perfil completo actualizado
            detail_serializer = PersonnelProfileDetailSerializer(
                profile,
                context={'request': request}
            )
            return Response({
                'message': 'Perfil actualizado exitosamente',
                'profile': detail_serializer.data
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def profile_completion_data(self, request):
        """
        Obtiene los datos necesarios para completar el perfil
        GET /api/personnel/profiles/profile_completion_data/

        Retorna:
        - Áreas disponibles
        - Centros de distribución disponibles
        - Opciones de jerarquía
        - Opciones de tipo de posición
        - Opciones de tipo de contrato
        - Opciones de género
        """
        from apps.maintenance.models import DistributorCenter

        data = {
            'areas': AreaSerializer(
                Area.objects.filter(is_active=True),
                many=True
            ).data,
            'distributor_centers': [
                {
                    'id': dc.id,
                    'name': dc.name,
                    'code': dc.country_code if hasattr(dc, 'country_code') else None
                }
                for dc in DistributorCenter.objects.all()
            ],
            'hierarchy_levels': [
                {'value': code, 'label': label}
                for code, label in PersonnelProfile.HIERARCHY_LEVEL_CHOICES
            ],
            'position_types': [
                {'value': code, 'label': label}
                for code, label in PersonnelProfile.POSITION_TYPE_CHOICES
            ],
            'contract_types': [
                {'value': 'PERMANENT', 'label': 'Permanente'},
                {'value': 'TEMPORARY', 'label': 'Temporal'},
                {'value': 'CONTRACT', 'label': 'Contrato'},
            ],
            'genders': [
                {'value': 'M', 'label': 'Masculino'},
                {'value': 'F', 'label': 'Femenino'},
                {'value': 'O', 'label': 'Otro'},
            ],
            'user_info': {
                'id': request.user.id,
                'username': request.user.username,
                'email': request.user.email,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
            }
        }

        return Response(data)

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """
        Dashboard con estadísticas generales
        GET /api/personnel/profiles/dashboard/
        """
        queryset = self.get_queryset()

        # Estadísticas básicas
        total_personnel = queryset.filter(is_active=True).count()
        total_inactive = queryset.filter(is_active=False).count()

        # Por jerarquía
        by_hierarchy = queryset.filter(is_active=True).values(
            'hierarchy_level'
        ).annotate(
            count=Count('id')
        )

        # Por área
        by_area = queryset.filter(is_active=True).values(
            'area__code',
            'area__name'
        ).annotate(
            count=Count('id')
        )

        # Certificaciones
        expiring_soon = queryset.filter(
            is_active=True,
            certifications__expiration_date__lte=date.today() + timedelta(days=30),
            certifications__expiration_date__gte=date.today(),
            certifications__is_valid=True
        ).distinct().count()

        expired = queryset.filter(
            is_active=True,
            certifications__expiration_date__lt=date.today(),
            certifications__is_valid=True
        ).distinct().count()

        # Nuevos ingresos (últimos 30 días)
        new_hires = queryset.filter(
            hire_date__gte=date.today() - timedelta(days=30)
        ).count()

        data = {
            'summary': {
                'total_active': total_personnel,
                'total_inactive': total_inactive,
                'new_hires_30_days': new_hires,
            },
            'by_hierarchy': list(by_hierarchy),
            'by_area': list(by_area),
            'certifications': {
                'expiring_soon': expiring_soon,
                'expired': expired,
            }
        }

        return Response(data)

    @action(detail=False, methods=['get'])
    def certifications_expiring(self, request):
        """
        Personal con certificaciones por vencer
        GET /api/personnel/profiles/certifications_expiring/

        Query params:
        - days: número de días (default: 30)
        """
        days = int(request.query_params.get('days', 30))
        threshold = date.today() + timedelta(days=days)

        queryset = self.get_queryset().filter(
            is_active=True,
            certifications__expiration_date__lte=threshold,
            certifications__expiration_date__gte=date.today(),
            certifications__is_valid=True
        ).distinct()

        serializer = PersonnelProfileListSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def supervised_personnel(self, request):
        """
        Personal que superviso directamente
        GET /api/personnel/profiles/supervised_personnel/
        """
        try:
            user_personnel = request.user.personnel_profile
            supervised = user_personnel.get_supervised_personnel()
            serializer = PersonnelProfileListSerializer(supervised, many=True)
            return Response(serializer.data)
        except PersonnelProfile.DoesNotExist:
            return Response(
                {'detail': 'No tiene un perfil de personal asociado'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['get'])
    def subordinates_tree(self, request, pk=None):
        """
        Árbol completo de subordinados (recursivo)
        GET /api/personnel/profiles/{id}/subordinates_tree/
        """
        personnel = self.get_object()

        def build_tree(person):
            supervised = person.get_supervised_personnel()
            return {
                'id': person.id,
                'employee_code': person.employee_code,
                'full_name': person.full_name,
                'position': person.position,
                'hierarchy_level': person.hierarchy_level,
                'subordinates': [build_tree(s) for s in supervised]
            }

        tree = build_tree(personnel)
        return Response(tree)

    @action(detail=True, methods=['get'])
    def performance_summary(self, request, pk=None):
        """
        Resumen de desempeño del personal
        GET /api/personnel/profiles/{id}/performance_summary/

        Query params:
        - period: DAILY|WEEKLY|MONTHLY (default: MONTHLY)
        - months: número de meses atrás (default: 3)
        """
        personnel = self.get_object()
        period = request.query_params.get('period', 'MONTHLY')
        months = int(request.query_params.get('months', 3))

        start_date = date.today() - timedelta(days=months * 30)

        metrics = personnel.performance_metrics.filter(
            period=period,
            metric_date__gte=start_date
        ).order_by('-metric_date')

        # Estadísticas agregadas
        stats = metrics.aggregate(
            avg_productivity=Avg('productivity_rate'),
            avg_rating=Avg('supervisor_rating'),
            total_pallets=Count('pallets_moved'),
            total_errors=Count('errors_count'),
            total_accidents=Count('accidents_count')
        )

        from ..serializers.performance_serializers import PerformanceMetricListSerializer

        data = {
            'personnel': {
                'id': personnel.id,
                'employee_code': personnel.employee_code,
                'full_name': personnel.full_name,
                'position': personnel.position
            },
            'period': period,
            'date_range': {
                'from': start_date,
                'to': date.today()
            },
            'statistics': stats,
            'metrics': PerformanceMetricListSerializer(metrics, many=True).data
        }

        return Response(data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, CanManagePersonnel])
    def users_without_profile(self, request):
        """
        Buscar usuarios que no tienen perfil de personal asociado
        GET /api/personnel/profiles/users_without_profile/

        Query params:
        - search: buscar por username, email, first_name, last_name
        """
        search = request.query_params.get('search', '')

        # Usuarios que NO tienen perfil de personal
        users = User.objects.filter(
            personnel_profile__isnull=True,
            is_active=True
        )

        if search:
            users = users.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )

        # Limitar a 20 resultados
        users = users[:20]

        data = [
            {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'full_name': user.get_full_name() or user.username,
                'centro_distribucion': user.centro_distribucion_id if hasattr(user, 'centro_distribucion') else None,
                'distributions_centers': list(user.distributions_centers.values_list('id', flat=True)) if hasattr(user, 'distributions_centers') else [],
            }
            for user in users
        ]

        return Response(data)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, CanManagePersonnel])
    def create_with_user(self, request):
        """
        Crear perfil de personal y usuario en una sola operación
        POST /api/personnel/profiles/create_with_user/

        Body:
        {
            "user_data": {
                "username": "jperez",
                "email": "jperez@example.com",
                "password": "password123",
                "first_name": "Juan",
                "last_name": "Pérez"
            },
            "profile_data": {
                "employee_code": "EMP001",
                ... resto de campos del perfil
            }
        }
        """
        user_data = request.data.get('user_data', {})
        profile_data = request.data.get('profile_data', {})

        if not user_data or not profile_data:
            return Response(
                {'detail': 'Se requiere user_data y profile_data'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validar campos requeridos del usuario
        required_user_fields = ['username', 'email', 'password']
        missing_fields = [field for field in required_user_fields if field not in user_data]
        if missing_fields:
            return Response(
                {'detail': f'Campos requeridos en user_data: {", ".join(missing_fields)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verificar que el username no exista
        if User.objects.filter(username=user_data['username']).exists():
            return Response(
                {'detail': 'El nombre de usuario ya existe'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verificar que el email no exista
        if User.objects.filter(email=user_data['email']).exists():
            return Response(
                {'detail': 'El email ya está registrado'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Crear el usuario
            user = User.objects.create_user(
                username=user_data['username'],
                email=user_data['email'],
                password=user_data['password'],
                first_name=user_data.get('first_name', ''),
                last_name=user_data.get('last_name', ''),
                is_active=user_data.get('is_active', True)
            )

            # Usar los nombres del usuario si no se proporcionan en profile_data
            if not profile_data.get('first_name'):
                profile_data['first_name'] = user.first_name
            if not profile_data.get('last_name'):
                profile_data['last_name'] = user.last_name
            if not profile_data.get('email'):
                profile_data['email'] = user.email

            # Crear el perfil vinculado al usuario
            serializer = PersonnelProfileCreateUpdateSerializer(data=profile_data)
            if serializer.is_valid():
                serializer.save(user=user, created_by=request.user)
                return Response(
                    {
                        'message': 'Usuario y perfil creados exitosamente',
                        'user': {
                            'id': user.id,
                            'username': user.username,
                            'email': user.email,
                        },
                        'profile': serializer.data
                    },
                    status=status.HTTP_201_CREATED
                )
            else:
                # Si falla la creación del perfil, eliminar el usuario creado
                user.delete()
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EmergencyContactViewSet(viewsets.ModelViewSet):
    """
    ViewSet para contactos de emergencia
    """
    queryset = EmergencyContact.objects.select_related('personnel')
    serializer_class = EmergencyContactSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['personnel', 'is_primary']

    def get_queryset(self):
        """Filtrar por permisos"""
        queryset = super().get_queryset()
        user = self.request.user

        try:
            user_personnel = user.personnel_profile
        except PersonnelProfile.DoesNotExist:
            return queryset.none()

        # Similar a PersonnelProfile - filtrar según jerarquía
        if user_personnel.hierarchy_level == PersonnelProfile.CD_MANAGER:
            return queryset.filter(
                personnel__primary_distributor_center=user_personnel.primary_distributor_center
            )

        if user_personnel.hierarchy_level == PersonnelProfile.AREA_MANAGER:
            return queryset.filter(personnel__area=user_personnel.area)

        if user_personnel.hierarchy_level == PersonnelProfile.SUPERVISOR:
            subordinates_ids = [p.id for p in user_personnel.get_all_subordinates()]
            return queryset.filter(
                Q(personnel=user_personnel) |
                Q(personnel__id__in=subordinates_ids)
            )

        return queryset.filter(personnel=user_personnel)
