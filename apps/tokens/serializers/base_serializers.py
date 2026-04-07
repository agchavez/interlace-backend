"""
Serializers base para el modelo TokenRequest
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from ..models import (
    TokenRequest, PermitHourDetail, PermitDayDetail, PermitDayDate,
    ExitPassDetail, ExitPassItem, Material, ExternalPerson,
    UniformDeliveryDetail, UniformItem,
    SubstitutionDetail, RateChangeDetail, OvertimeDetail, ShiftChangeDetail
)
from ..services.approval_service import ApprovalLevelService
from apps.personnel.models import PersonnelProfile
from apps.maintenance.models import DistributorCenter

User = get_user_model()


class PersonnelBasicSerializer(serializers.ModelSerializer):
    """Serializer básico para PersonnelProfile"""
    full_name = serializers.CharField(read_only=True)
    area_name = serializers.SerializerMethodField()
    position_display = serializers.CharField(source='get_position_type_display', read_only=True)

    def get_area_name(self, obj):
        if obj.area:
            return obj.area.name if hasattr(obj.area, 'name') else str(obj.area)
        return None

    class Meta:
        model = PersonnelProfile
        fields = [
            'id', 'employee_code', 'first_name', 'last_name', 'full_name',
            'area_name', 'position_type', 'position_display', 'hierarchy_level'
        ]
        read_only_fields = fields


class UserBasicSerializer(serializers.ModelSerializer):
    """Serializer básico para User"""
    full_name = serializers.SerializerMethodField()

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.email

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'full_name']
        read_only_fields = fields


class DistributorCenterBasicSerializer(serializers.ModelSerializer):
    """Serializer básico para DistributorCenter"""
    class Meta:
        model = DistributorCenter
        fields = ['id', 'name']
        read_only_fields = fields


class TokenRequestListSerializer(serializers.ModelSerializer):
    """Serializer para listado de tokens"""
    personnel_name = serializers.SerializerMethodField()
    personnel_code = serializers.CharField(source='personnel.employee_code', read_only=True)
    requested_by_name = serializers.SerializerMethodField()

    def get_personnel_name(self, obj):
        if obj.personnel:
            return obj.personnel.full_name
        # Para tokens de personas externas, buscar en exit_pass_detail
        try:
            ep = obj.exit_pass_detail.external_person
            if ep:
                return f"{ep.name} (Externo)"
        except Exception:
            pass
        return None

    def get_requested_by_name(self, obj):
        if obj.requested_by:
            return f"{obj.requested_by.first_name} {obj.requested_by.last_name}".strip() or obj.requested_by.email
        return None
    distributor_center_name = serializers.CharField(source='distributor_center.name', read_only=True)
    token_type_display = serializers.CharField(source='get_token_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    current_approval_level = serializers.IntegerField(source='get_current_approval_level', read_only=True)

    class Meta:
        model = TokenRequest
        fields = [
            'id', 'token_code', 'display_number',
            'token_type', 'token_type_display',
            'status', 'status_display',
            'personnel', 'personnel_name', 'personnel_code',
            'requested_by', 'requested_by_name',
            'distributor_center', 'distributor_center_name',
            'valid_from', 'valid_until',
            'approval_progress', 'current_approval_level',
            'created_at',
        ]
        read_only_fields = fields


class TokenRequestDetailSerializer(serializers.ModelSerializer):
    """Serializer completo para detalle de token"""
    personnel = PersonnelBasicSerializer(read_only=True)
    requested_by = UserBasicSerializer(read_only=True)
    requested_by_name = serializers.SerializerMethodField()
    distributor_center = DistributorCenterBasicSerializer(read_only=True)
    token_type_display = serializers.CharField(source='get_token_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    def get_requested_by_name(self, obj):
        if obj.requested_by:
            return f"{obj.requested_by.first_name} {obj.requested_by.last_name}".strip() or obj.requested_by.email
        return None

    # Aprobaciones
    approved_level_1_by = PersonnelBasicSerializer(read_only=True)
    approved_level_2_by = PersonnelBasicSerializer(read_only=True)
    approved_level_3_by = PersonnelBasicSerializer(read_only=True)
    rejected_by = PersonnelBasicSerializer(read_only=True)
    validated_by = PersonnelBasicSerializer(read_only=True)

    # Image fields with SAS tokens - approval signatures/photos
    approved_level_1_signature = serializers.SerializerMethodField()
    approved_level_1_photo = serializers.SerializerMethodField()
    approved_level_2_signature = serializers.SerializerMethodField()
    approved_level_2_photo = serializers.SerializerMethodField()
    approved_level_3_signature = serializers.SerializerMethodField()
    approved_level_3_photo = serializers.SerializerMethodField()
    # Validation signature/photo
    validation_signature = serializers.SerializerMethodField()
    validation_photo = serializers.SerializerMethodField()

    # Propiedades calculadas
    current_approval_level = serializers.IntegerField(source='get_current_approval_level', read_only=True)
    is_valid = serializers.BooleanField(read_only=True)
    can_be_used = serializers.BooleanField(read_only=True)
    requires_validation = serializers.BooleanField(read_only=True)
    validation_type = serializers.CharField(read_only=True)

    # User-specific permissions
    can_user_approve = serializers.SerializerMethodField()
    can_user_complete_delivery = serializers.SerializerMethodField()
    can_user_validate = serializers.SerializerMethodField()

    def get_can_user_approve(self, obj):
        """Check if current user can approve this token at the current level"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        try:
            personnel = request.user.personnel_profile
            current_level = obj.get_current_approval_level()
            if not current_level:
                return False
            return obj.can_user_approve(personnel, current_level)
        except:
            return False

    def get_can_user_complete_delivery(self, obj):
        """Check if current user can complete uniform delivery"""
        if obj.token_type != 'UNIFORM_DELIVERY':
            return False
        if obj.status != 'APPROVED':
            return False
        if not hasattr(obj, 'uniform_delivery_detail') or obj.uniform_delivery_detail.is_delivered:
            return False
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        try:
            personnel = request.user.personnel_profile
            # Supervisors and Area Managers can complete delivery
            return personnel.hierarchy_level in ['SUPERVISOR', 'AREA_MANAGER', 'CD_MANAGER']
        except:
            return False

    def get_can_user_validate(self, obj):
        """
        Check if current user can validate/mark this token as used.
        - Security: can_validate_token permission (EXIT_PASS only)
        - Payroll: can_validate_payroll permission (PERMIT_HOUR, OVERTIME, etc.)
        """
        # Solo tokens aprobados y válidos pueden ser validados
        if not obj.can_be_used:
            return False
        # Solo tokens que requieren validación
        if not obj.requires_validation:
            return False

        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False

        user = request.user
        validation_type = obj.validation_type

        if validation_type == 'security':
            return user.has_perm('tokens.can_validate_token')
        elif validation_type == 'payroll':
            return user.has_perm('tokens.can_validate_payroll')

        return False

    # Approval signature/photo getters with SAS tokens
    def get_approved_level_1_signature(self, obj):
        from apps.core.azure_utils import get_photo_url_with_sas
        return get_photo_url_with_sas(obj.approved_level_1_signature)

    def get_approved_level_1_photo(self, obj):
        from apps.core.azure_utils import get_photo_url_with_sas
        return get_photo_url_with_sas(obj.approved_level_1_photo)

    def get_approved_level_2_signature(self, obj):
        from apps.core.azure_utils import get_photo_url_with_sas
        return get_photo_url_with_sas(obj.approved_level_2_signature)

    def get_approved_level_2_photo(self, obj):
        from apps.core.azure_utils import get_photo_url_with_sas
        return get_photo_url_with_sas(obj.approved_level_2_photo)

    def get_approved_level_3_signature(self, obj):
        from apps.core.azure_utils import get_photo_url_with_sas
        return get_photo_url_with_sas(obj.approved_level_3_signature)

    def get_approved_level_3_photo(self, obj):
        from apps.core.azure_utils import get_photo_url_with_sas
        return get_photo_url_with_sas(obj.approved_level_3_photo)

    # Validation signature/photo getters with SAS tokens
    def get_validation_signature(self, obj):
        from apps.core.azure_utils import get_photo_url_with_sas
        return get_photo_url_with_sas(obj.validation_signature)

    def get_validation_photo(self, obj):
        from apps.core.azure_utils import get_photo_url_with_sas
        return get_photo_url_with_sas(obj.validation_photo)

    # Detalle específico del tipo de token
    permit_hour_detail = serializers.SerializerMethodField()
    permit_day_detail = serializers.SerializerMethodField()
    exit_pass_detail = serializers.SerializerMethodField()
    uniform_delivery_detail = serializers.SerializerMethodField()
    substitution_detail = serializers.SerializerMethodField()
    rate_change_detail = serializers.SerializerMethodField()
    overtime_detail = serializers.SerializerMethodField()
    shift_change_detail = serializers.SerializerMethodField()

    class Meta:
        model = TokenRequest
        fields = [
            'id', 'token_code', 'display_number',
            'token_type', 'token_type_display',
            'status', 'status_display',
            'personnel', 'requested_by', 'requested_by_name', 'distributor_center',
            'qr_code_url',
            'requires_level_1', 'requires_level_2', 'requires_level_3',
            'approved_level_1_by', 'approved_level_1_at', 'approved_level_1_notes',
            'approved_level_1_signature', 'approved_level_1_photo',
            'approved_level_2_by', 'approved_level_2_at', 'approved_level_2_notes',
            'approved_level_2_signature', 'approved_level_2_photo',
            'approved_level_3_by', 'approved_level_3_at', 'approved_level_3_notes',
            'approved_level_3_signature', 'approved_level_3_photo',
            'rejected_by', 'rejected_at', 'rejection_reason',
            'validated_by', 'validated_at',
            'validation_signature', 'validation_photo', 'validation_notes',
            'valid_from', 'valid_until',
            'requester_notes', 'internal_notes',
            'approval_progress', 'current_approval_level',
            'is_valid', 'can_be_used', 'requires_validation', 'validation_type',
            'can_user_approve', 'can_user_complete_delivery', 'can_user_validate',
            'created_at',
            # Detalles específicos
            'permit_hour_detail',
            'permit_day_detail',
            'exit_pass_detail',
            'uniform_delivery_detail',
            'substitution_detail',
            'rate_change_detail',
            'overtime_detail',
            'shift_change_detail',
        ]
        read_only_fields = fields

    def get_permit_hour_detail(self, obj):
        """Retorna el detalle de permiso por hora si aplica"""
        if obj.token_type == TokenRequest.TokenType.PERMIT_HOUR:
            try:
                from .token_type_serializers import PermitHourDetailSerializer
                return PermitHourDetailSerializer(obj.permit_hour_detail).data
            except PermitHourDetail.DoesNotExist:
                return None
        return None

    def get_permit_day_detail(self, obj):
        """Retorna el detalle de permiso por día si aplica"""
        if obj.token_type == TokenRequest.TokenType.PERMIT_DAY:
            try:
                from .token_type_serializers import PermitDayDetailSerializer
                return PermitDayDetailSerializer(obj.permit_day_detail).data
            except PermitDayDetail.DoesNotExist:
                return None
        return None

    def get_exit_pass_detail(self, obj):
        """Retorna el detalle de pase de salida si aplica"""
        if obj.token_type == TokenRequest.TokenType.EXIT_PASS:
            try:
                from .token_type_serializers import ExitPassDetailSerializer
                return ExitPassDetailSerializer(obj.exit_pass_detail).data
            except ExitPassDetail.DoesNotExist:
                return None
        return None

    def get_uniform_delivery_detail(self, obj):
        """Retorna el detalle de entrega de uniforme si aplica"""
        if obj.token_type == TokenRequest.TokenType.UNIFORM_DELIVERY:
            try:
                from .token_type_serializers import UniformDeliveryDetailSerializer
                return UniformDeliveryDetailSerializer(obj.uniform_delivery_detail).data
            except UniformDeliveryDetail.DoesNotExist:
                return None
        return None

    def get_substitution_detail(self, obj):
        """Retorna el detalle de sustitución si aplica"""
        if obj.token_type == TokenRequest.TokenType.SUBSTITUTION:
            try:
                from .token_type_serializers import SubstitutionDetailSerializer
                return SubstitutionDetailSerializer(obj.substitution_detail).data
            except SubstitutionDetail.DoesNotExist:
                return None
        return None

    def get_rate_change_detail(self, obj):
        """Retorna el detalle de cambio de tasa si aplica"""
        if obj.token_type == TokenRequest.TokenType.RATE_CHANGE:
            try:
                from .token_type_serializers import RateChangeDetailSerializer
                return RateChangeDetailSerializer(obj.rate_change_detail).data
            except RateChangeDetail.DoesNotExist:
                return None
        return None

    def get_overtime_detail(self, obj):
        """Retorna el detalle de horas extra si aplica"""
        if obj.token_type == TokenRequest.TokenType.OVERTIME:
            try:
                from .token_type_serializers import OvertimeDetailSerializer
                return OvertimeDetailSerializer(obj.overtime_detail).data
            except OvertimeDetail.DoesNotExist:
                return None
        return None

    def get_shift_change_detail(self, obj):
        """Retorna el detalle de cambio de turno si aplica"""
        if obj.token_type == TokenRequest.TokenType.SHIFT_CHANGE:
            try:
                from .token_type_serializers import ShiftChangeDetailSerializer
                return ShiftChangeDetailSerializer(obj.shift_change_detail).data
            except ShiftChangeDetail.DoesNotExist:
                return None
        return None


class TokenRequestCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear tokens"""
    permit_hour_detail = serializers.DictField(required=False, write_only=True)
    permit_day_detail = serializers.DictField(required=False, write_only=True)
    exit_pass_detail = serializers.DictField(required=False, write_only=True)
    uniform_delivery_detail = serializers.DictField(required=False, write_only=True)
    substitution_detail = serializers.DictField(required=False, write_only=True)
    rate_change_detail = serializers.DictField(required=False, write_only=True)
    overtime_detail = serializers.DictField(required=False, write_only=True)
    shift_change_detail = serializers.DictField(required=False, write_only=True)

    class Meta:
        model = TokenRequest
        fields = [
            'token_type', 'personnel', 'distributor_center',
            'valid_from', 'valid_until',
            'requires_level_1', 'requires_level_2', 'requires_level_3',
            'requester_notes',
            # Detalles específicos
            'permit_hour_detail',
            'permit_day_detail',
            'exit_pass_detail',
            'uniform_delivery_detail',
            'substitution_detail',
            'rate_change_detail',
            'overtime_detail',
            'shift_change_detail',
        ]

    def validate(self, data):
        """Validaciones generales"""
        token_type = data.get('token_type')
        personnel = data.get('personnel')

        # Mapeo de tipo a campo de detalle requerido
        type_detail_map = {
            TokenRequest.TokenType.PERMIT_HOUR: 'permit_hour_detail',
            TokenRequest.TokenType.PERMIT_DAY: 'permit_day_detail',
            TokenRequest.TokenType.EXIT_PASS: 'exit_pass_detail',
            TokenRequest.TokenType.UNIFORM_DELIVERY: 'uniform_delivery_detail',
            TokenRequest.TokenType.SUBSTITUTION: 'substitution_detail',
            TokenRequest.TokenType.RATE_CHANGE: 'rate_change_detail',
            TokenRequest.TokenType.OVERTIME: 'overtime_detail',
            TokenRequest.TokenType.SHIFT_CHANGE: 'shift_change_detail',
        }

        detail_field = type_detail_map.get(token_type)
        if detail_field and not data.get(detail_field):
            raise serializers.ValidationError({
                detail_field: f'Este campo es requerido para {token_type}.'
            })

        # Validar que uniform delivery tenga al menos un item
        if token_type == TokenRequest.TokenType.UNIFORM_DELIVERY:
            uniform_data = data.get('uniform_delivery_detail', {})
            if not uniform_data.get('items'):
                raise serializers.ValidationError({
                    'uniform_delivery_detail': 'Debe incluir al menos un artículo para la entrega de uniforme.'
                })

        # Validar que tokens de dos niveles solo sean para operativos
        if token_type in ApprovalLevelService.TWO_LEVEL_TYPES:
            if personnel and personnel.hierarchy_level != PersonnelProfile.OPERATIVE:
                raise serializers.ValidationError({
                    'personnel': f'El tipo de token {token_type} solo está permitido para personal operativo.'
                })

        # Validar fechas
        valid_from = data.get('valid_from')
        valid_until = data.get('valid_until')
        if valid_from and valid_until and valid_from >= valid_until:
            raise serializers.ValidationError({
                'valid_until': 'La fecha de fin debe ser posterior a la fecha de inicio.'
            })

        return data

    def create(self, validated_data):
        """Crear token con su detalle específico"""
        # Extraer todos los detalles
        permit_hour_data = validated_data.pop('permit_hour_detail', None)
        permit_day_data = validated_data.pop('permit_day_detail', None)
        exit_pass_data = validated_data.pop('exit_pass_detail', None)
        uniform_delivery_data = validated_data.pop('uniform_delivery_detail', None)
        substitution_data = validated_data.pop('substitution_detail', None)
        rate_change_data = validated_data.pop('rate_change_detail', None)
        overtime_data = validated_data.pop('overtime_detail', None)
        shift_change_data = validated_data.pop('shift_change_detail', None)

        # Obtener tipo de token y beneficiario
        token_type = validated_data.get('token_type')
        personnel = validated_data.get('personnel')

        # Determinar si es pase de salida para externos
        is_external = False
        if token_type == TokenRequest.TokenType.EXIT_PASS and exit_pass_data:
            is_external = exit_pass_data.get('is_external', False)

        # Determinar niveles de aprobación según tipo y jerarquía del beneficiario
        beneficiary_hierarchy = personnel.hierarchy_level if personnel else None

        requires_l1, requires_l2, requires_l3, initial_status = ApprovalLevelService.determine_approval_levels(
            token_type,
            beneficiary_hierarchy,
            is_external
        )

        validated_data['requires_level_1'] = requires_l1
        validated_data['requires_level_2'] = requires_l2
        validated_data['requires_level_3'] = requires_l3
        validated_data['status'] = initial_status

        # Crear el token base
        token = TokenRequest.objects.create(**validated_data)

        # Crear detalle específico según tipo
        if token.token_type == TokenRequest.TokenType.PERMIT_HOUR and permit_hour_data:
            PermitHourDetail.objects.create(token=token, **permit_hour_data)

        elif token.token_type == TokenRequest.TokenType.PERMIT_DAY and permit_day_data:
            selected_dates = permit_day_data.pop('selected_dates', [])
            detail = PermitDayDetail.objects.create(token=token, **permit_day_data)
            for date_val in selected_dates:
                PermitDayDate.objects.create(permit_day=detail, date=date_val)

        elif token.token_type == TokenRequest.TokenType.EXIT_PASS and exit_pass_data:
            items_data = exit_pass_data.pop('items', [])
            external_person_id = exit_pass_data.pop('external_person', None)
            if external_person_id:
                exit_pass_data['external_person'] = ExternalPerson.objects.get(pk=external_person_id)
            detail = ExitPassDetail.objects.create(token=token, **exit_pass_data)
            for item_data in items_data:
                material_id = item_data.pop('material', None)
                product_id = item_data.pop('product', None)
                if material_id:
                    item_data['material'] = Material.objects.get(pk=material_id)
                if product_id:
                    from apps.maintenance.models import ProductModel
                    item_data['product'] = ProductModel.objects.get(pk=product_id)
                ExitPassItem.objects.create(exit_pass=detail, **item_data)
            # Si el valor total es muy alto, agregar aprobación de nivel 3
            if detail.requires_level_3_approval:
                token.requires_level_3 = True
                token.save()

        elif token.token_type == TokenRequest.TokenType.UNIFORM_DELIVERY and uniform_delivery_data:
            items_data = uniform_delivery_data.pop('items', [])
            detail = UniformDeliveryDetail.objects.create(token=token, **uniform_delivery_data)
            for item_data in items_data:
                material_id = item_data.pop('material', None)
                if material_id:
                    item_data['material_id'] = material_id
                UniformItem.objects.create(uniform_delivery=detail, **item_data)
            # UNIFORM_DELIVERY: Ya está configurado como APPROVED por ApprovalLevelService

        elif token.token_type == TokenRequest.TokenType.SUBSTITUTION and substitution_data:
            substituted_id = substitution_data.pop('substituted_personnel')
            substitution_data['substituted_personnel'] = PersonnelProfile.objects.get(
                pk=substituted_id
            )
            SubstitutionDetail.objects.create(token=token, **substitution_data)

        elif token.token_type == TokenRequest.TokenType.RATE_CHANGE and rate_change_data:
            RateChangeDetail.objects.create(token=token, **rate_change_data)

        elif token.token_type == TokenRequest.TokenType.OVERTIME and overtime_data:
            from datetime import datetime, time, date as date_type
            from ..models import OvertimeSegment
            # Extract segments before creating detail
            segments_data = overtime_data.pop('segments', [])
            # Convert FK IDs to _id fields for proper assignment
            overtime_type_model_id = overtime_data.pop('overtime_type_model', None)
            reason_model_id = overtime_data.pop('reason_model', None)
            if overtime_type_model_id:
                overtime_data['overtime_type_model_id'] = overtime_type_model_id
            if reason_model_id:
                overtime_data['reason_model_id'] = reason_model_id
            # Parse string fields to proper types (data comes from DictField, not typed serializer)
            if isinstance(overtime_data.get('start_time'), str):
                overtime_data['start_time'] = datetime.strptime(overtime_data['start_time'], '%H:%M').time()
            if isinstance(overtime_data.get('end_time'), str):
                overtime_data['end_time'] = datetime.strptime(overtime_data['end_time'], '%H:%M').time()
            if isinstance(overtime_data.get('overtime_date'), str):
                overtime_data['overtime_date'] = datetime.strptime(overtime_data['overtime_date'], '%Y-%m-%d').date()
            detail = OvertimeDetail.objects.create(token=token, **overtime_data)
            # Create segments if provided (variable rate)
            for idx, seg in enumerate(segments_data):
                seg_type_model_id = seg.pop('overtime_type_model', None)
                if isinstance(seg.get('start_time'), str):
                    seg['start_time'] = datetime.strptime(seg['start_time'], '%H:%M').time()
                if isinstance(seg.get('end_time'), str):
                    seg['end_time'] = datetime.strptime(seg['end_time'], '%H:%M').time()
                seg['sequence'] = seg.get('sequence', idx)
                segment = OvertimeSegment(
                    overtime_detail=detail,
                    **seg,
                )
                if seg_type_model_id:
                    segment.overtime_type_model_id = seg_type_model_id
                segment.save()
            # Recalculate totals from segments
            if segments_data:
                detail.recalculate_totals()

        elif token.token_type == TokenRequest.TokenType.SHIFT_CHANGE and shift_change_data:
            exchange_with_id = shift_change_data.pop('exchange_with', None)
            if exchange_with_id:
                shift_change_data['exchange_with'] = PersonnelProfile.objects.get(
                    pk=exchange_with_id
                )
            ShiftChangeDetail.objects.create(token=token, **shift_change_data)

        return token


class BulkOvertimeCreateSerializer(serializers.Serializer):
    """Serializer para creación masiva de tokens de horas extra"""
    personnel_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        max_length=200,
    )
    distributor_center = serializers.PrimaryKeyRelatedField(
        queryset=DistributorCenter.objects.all()
    )
    valid_from = serializers.DateTimeField()
    valid_until = serializers.DateTimeField()
    requester_notes = serializers.CharField(required=False, allow_blank=True, default='')
    overtime_detail = serializers.DictField(required=True)

    def validate_personnel_ids(self, value):
        seen = set()
        unique = []
        for pid in value:
            if pid not in seen:
                seen.add(pid)
                unique.append(pid)
        existing = set(
            PersonnelProfile.objects.filter(id__in=unique, is_active=True).values_list('id', flat=True)
        )
        not_found = [pid for pid in unique if pid not in existing]
        if not_found:
            raise serializers.ValidationError(f'IDs no encontrados o inactivos: {not_found}')
        return unique

    def validate(self, data):
        if data['valid_from'] >= data['valid_until']:
            raise serializers.ValidationError({
                'valid_until': 'Debe ser posterior a valid_from.'
            })
        return data


class TokenApprovalSerializer(serializers.Serializer):
    """Serializer para aprobar un token con firma y foto opcionales"""
    notes = serializers.CharField(required=False, allow_blank=True, max_length=500)
    signature = serializers.ImageField(required=False, allow_null=True)
    photo = serializers.ImageField(required=False, allow_null=True)


class TokenRejectSerializer(serializers.Serializer):
    """Serializer para rechazar un token"""
    reason = serializers.CharField(required=True, max_length=1000)


class TokenValidateSerializer(serializers.Serializer):
    """Serializer para validar un token con firma y foto opcionales"""
    token_code = serializers.CharField(required=True)
    notes = serializers.CharField(required=False, allow_blank=True, max_length=500)
    signature = serializers.ImageField(required=False, allow_null=True)
    photo = serializers.ImageField(required=False, allow_null=True)


class PublicTokenSerializer(serializers.ModelSerializer):
    """
    Serializer para vista pública del token (sin autenticación).
    Muestra información limitada y segura.
    """
    personnel_name = serializers.CharField(source='personnel.full_name', read_only=True)
    personnel_code = serializers.CharField(source='personnel.employee_code', read_only=True)
    personnel_area = serializers.SerializerMethodField()
    distributor_center_name = serializers.CharField(source='distributor_center.name', read_only=True)
    token_type_display = serializers.CharField(source='get_token_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    # Detalle según tipo
    detail_summary = serializers.SerializerMethodField()

    def get_personnel_area(self, obj):
        """Obtener el área del personal de forma segura"""
        if obj.personnel and obj.personnel.area:
            return obj.personnel.area.name
        return None

    class Meta:
        model = TokenRequest
        fields = [
            'id',
            'display_number', 'token_code',
            'token_type', 'token_type_display',
            'status', 'status_display',
            'personnel_name', 'personnel_code', 'personnel_area',
            'distributor_center_name',
            'valid_from', 'valid_until',
            'validated_at',
            'qr_code_url',
            'detail_summary',
        ]
        read_only_fields = fields

    def get_detail_summary(self, obj):
        """Retorna un resumen del detalle según el tipo de token con etiquetas en español"""
        try:
            if obj.token_type == TokenRequest.TokenType.PERMIT_HOUR:
                detail = obj.permit_hour_detail
                return {
                    'Motivo': detail.get_reason_type_display(),
                    'Horas Solicitadas': f"{detail.hours_requested}h",
                    'Hora de Salida': detail.exit_time.strftime('%H:%M') if detail.exit_time else '-',
                    'Hora de Retorno': detail.expected_return_time.strftime('%H:%M') if detail.expected_return_time else '-',
                    'Con Goce de Sueldo': 'Sí' if detail.with_pay else 'No',
                }

            elif obj.token_type == TokenRequest.TokenType.PERMIT_DAY:
                detail = obj.permit_day_detail
                return {
                    'Motivo': detail.get_reason_display(),
                    'Total de Días': str(detail.total_days),
                    'Tipo de Selección': detail.get_date_selection_type_display(),
                    'Con Goce de Sueldo': 'Sí' if detail.with_pay else 'No',
                }

            elif obj.token_type == TokenRequest.TokenType.EXIT_PASS:
                detail = obj.exit_pass_detail
                return {
                    'Destino': detail.destination,
                    'Propósito': detail.purpose,
                    'Total de Artículos': str(detail.items.count()),
                    'Valor Total': f"L. {detail.total_value:,.2f}",
                }

            elif obj.token_type == TokenRequest.TokenType.UNIFORM_DELIVERY:
                detail = obj.uniform_delivery_detail
                return {
                    'Total de Artículos': str(detail.items.count()),
                    'Estado': 'Entregado' if detail.is_delivered else 'Pendiente',
                    'Lugar de Entrega': detail.delivery_location or '-',
                }

            elif obj.token_type == TokenRequest.TokenType.SUBSTITUTION:
                detail = obj.substitution_detail
                return {
                    'Sustituye a': detail.substituted_personnel.get_full_name(),
                    'Motivo': detail.get_reason_display(),
                    'Total de Días': str(detail.total_days),
                }

            elif obj.token_type == TokenRequest.TokenType.RATE_CHANGE:
                detail = obj.rate_change_detail
                return {
                    'Motivo': detail.get_reason_display(),
                    'Tasa Actual': f"L. {detail.current_rate:,.2f}",
                    'Nueva Tasa': f"L. {detail.new_rate:,.2f}",
                    'Diferencia': f"L. {detail.rate_difference:,.2f}",
                }

            elif obj.token_type == TokenRequest.TokenType.OVERTIME:
                detail = obj.overtime_detail
                tipo = detail.overtime_type_model.name if detail.overtime_type_model else detail.get_overtime_type_display()
                motivo = detail.reason_model.name if detail.reason_model else detail.get_reason_display()
                total_h = detail.total_hours
                total_str = f"{int(total_h)}h" if total_h == int(total_h) else f"{total_h}h"
                mult = detail.pay_multiplier
                mult_str = f"x{int(mult)}" if mult == int(mult) else f"x{mult}"
                return {
                    'Tipo': tipo,
                    'Motivo': motivo,
                    'Fecha': detail.overtime_date.strftime('%d %b %Y'),
                    'Horario': f"{detail.start_time.strftime('%H:%M')} – {detail.end_time.strftime('%H:%M')}",
                    'Duración': total_str,
                    'Multiplicador': mult_str,
                }

            elif obj.token_type == TokenRequest.TokenType.SHIFT_CHANGE:
                detail = obj.shift_change_detail
                return {
                    'Motivo': detail.get_reason_display(),
                    'Turno Actual': detail.current_shift_name,
                    'Nuevo Turno': detail.new_shift_name,
                    'Fecha de Cambio': detail.change_date.strftime('%d/%m/%Y'),
                    'Permanente': 'Sí' if detail.is_permanent else 'No',
                }
        except Exception:
            return None

        return None
