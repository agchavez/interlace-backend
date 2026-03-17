"""
Serializers específicos para cada tipo de token
"""
from rest_framework import serializers
from ..models import (
    PermitHourDetail, PermitDayDetail, PermitDayDate,
    ExitPassDetail, ExitPassItem, Material, UnitOfMeasure,
    UniformDeliveryDetail, UniformItem,
    SubstitutionDetail, RateChangeDetail, OvertimeDetail, ShiftChangeDetail,
    OvertimeTypeModel, OvertimeReasonModel,
)
from apps.personnel.models import PersonnelProfile
from .external_person_serializers import ExternalPersonBasicSerializer


# ============ CATALOG SERIALIZERS ============

class UnitOfMeasureSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitOfMeasure
        fields = ['id', 'code', 'name', 'abbreviation']
        read_only_fields = ['id']


class MaterialSerializer(serializers.ModelSerializer):
    unit_of_measure_name = serializers.CharField(
        source='unit_of_measure.name', read_only=True
    )

    class Meta:
        model = Material
        fields = [
            'id', 'code', 'name', 'description',
            'unit_of_measure', 'unit_of_measure_name',
            'unit_value', 'requires_return', 'category'
        ]
        read_only_fields = ['id']


class OvertimeTypeModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = OvertimeTypeModel
        fields = ['id', 'code', 'name', 'description', 'default_multiplier', 'is_active']
        read_only_fields = ['id']


class OvertimeReasonModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = OvertimeReasonModel
        fields = ['id', 'code', 'name', 'description', 'is_active']
        read_only_fields = ['id']


# ============ PERMIT HOUR ============

class PermitHourDetailSerializer(serializers.ModelSerializer):
    reason_type_display = serializers.CharField(
        source='get_reason_type_display', read_only=True
    )

    class Meta:
        model = PermitHourDetail
        fields = [
            'id', 'reason_type', 'reason_type_display', 'reason_detail',
            'exit_time', 'expected_return_time', 'hours_requested',
            'with_pay', 'destination'
        ]
        read_only_fields = ['id']


# ============ PERMIT DAY ============

class PermitDayDateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PermitDayDate
        fields = ['id', 'date', 'notes']
        read_only_fields = ['id']


class PermitDayDetailSerializer(serializers.ModelSerializer):
    date_selection_type_display = serializers.CharField(
        source='get_date_selection_type_display', read_only=True
    )
    reason_display = serializers.CharField(
        source='get_reason_display', read_only=True
    )
    selected_dates = PermitDayDateSerializer(many=True, read_only=True)
    total_days = serializers.IntegerField(read_only=True)

    class Meta:
        model = PermitDayDetail
        fields = [
            'id', 'date_selection_type', 'date_selection_type_display',
            'reason', 'reason_display', 'reason_detail',
            'with_pay', 'start_date', 'end_date',
            'selected_dates', 'total_days'
        ]
        read_only_fields = ['id', 'total_days']


class PermitDayDetailCreateSerializer(serializers.Serializer):
    """Serializer para crear permiso por día"""
    date_selection_type = serializers.ChoiceField(
        choices=PermitDayDetail.DateSelectionType.choices
    )
    reason = serializers.ChoiceField(
        choices=PermitDayDetail.PermitReason.choices
    )
    reason_detail = serializers.CharField(required=False, allow_blank=True)
    with_pay = serializers.BooleanField(default=True)
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    selected_dates = serializers.ListField(
        child=serializers.DateField(), required=False
    )

    def validate(self, data):
        selection_type = data.get('date_selection_type')

        if selection_type == PermitDayDetail.DateSelectionType.RANGE:
            if not data.get('start_date') or not data.get('end_date'):
                raise serializers.ValidationError(
                    'start_date y end_date son requeridos para rango de fechas.'
                )
            if data['start_date'] > data['end_date']:
                raise serializers.ValidationError(
                    'start_date debe ser anterior a end_date.'
                )

        if selection_type == PermitDayDetail.DateSelectionType.MULTIPLE:
            if not data.get('selected_dates'):
                raise serializers.ValidationError(
                    'selected_dates es requerido para días múltiples.'
                )

        return data


# ============ EXIT PASS ============

class ExitPassItemSerializer(serializers.ModelSerializer):
    material_name = serializers.CharField(
        source='material.name', read_only=True
    )
    product_name = serializers.CharField(
        source='product.name', read_only=True
    )
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = ExitPassItem
        fields = [
            'id', 'material', 'material_name', 'product', 'product_name',
            'custom_description', 'quantity', 'unit_value', 'total_value',
            'requires_return', 'return_date', 'returned', 'returned_at',
            'returned_quantity', 'return_notes', 'is_overdue'
        ]
        read_only_fields = ['id', 'total_value', 'is_overdue']


class ExitPassDetailSerializer(serializers.ModelSerializer):
    items = ExitPassItemSerializer(many=True, read_only=True)
    total_value = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    requires_level_3_approval = serializers.BooleanField(read_only=True)
    external_person = ExternalPersonBasicSerializer(read_only=True)

    class Meta:
        model = ExitPassDetail
        fields = [
            'id', 'destination', 'purpose', 'vehicle_plate', 'driver_name',
            'expected_return_date', 'is_external', 'external_person',
            'items', 'total_value', 'requires_level_3_approval'
        ]
        read_only_fields = ['id', 'total_value', 'requires_level_3_approval']


class ExitPassItemCreateSerializer(serializers.Serializer):
    """Serializer para crear item de pase de salida"""
    material = serializers.IntegerField(required=False)
    product = serializers.IntegerField(required=False)
    custom_description = serializers.CharField(required=False, allow_blank=True)
    quantity = serializers.DecimalField(max_digits=10, decimal_places=2)
    unit_value = serializers.DecimalField(max_digits=10, decimal_places=2)
    requires_return = serializers.BooleanField(default=False)
    return_date = serializers.DateField(required=False)

    def validate(self, data):
        if not data.get('material') and not data.get('product') and not data.get('custom_description'):
            raise serializers.ValidationError(
                'Debe especificar material, producto o descripción personalizada.'
            )
        return data


class ExitPassDetailCreateSerializer(serializers.Serializer):
    """Serializer para crear pase de salida"""
    destination = serializers.CharField(max_length=255)
    purpose = serializers.CharField()
    vehicle_plate = serializers.CharField(required=False, allow_blank=True)
    driver_name = serializers.CharField(required=False, allow_blank=True)
    expected_return_date = serializers.DateField(required=False)
    is_external = serializers.BooleanField(default=False)
    external_person = serializers.IntegerField(required=False, allow_null=True)
    items = ExitPassItemCreateSerializer(many=True)

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError('Debe incluir al menos un item.')
        return value


# ============ UNIFORM DELIVERY ============

class UniformItemSerializer(serializers.ModelSerializer):
    item_type_display = serializers.CharField(
        source='get_item_type_display', read_only=True, default=''
    )
    size_display = serializers.CharField(
        source='get_size_display', read_only=True
    )
    material_name = serializers.CharField(
        source='material.name', read_only=True, default=None
    )
    material_code = serializers.CharField(
        source='material.code', read_only=True, default=None
    )
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = UniformItem
        fields = [
            'id', 'material', 'material_name', 'material_code',
            'item_type', 'item_type_display',
            'custom_description', 'size', 'size_display', 'color',
            'quantity', 'requires_return', 'return_date',
            'returned', 'returned_at', 'is_overdue'
        ]
        read_only_fields = ['id', 'is_overdue']


class UniformDeliveryDetailSerializer(serializers.ModelSerializer):
    items = UniformItemSerializer(many=True, read_only=True)
    delivered_by_name = serializers.CharField(
        source='delivered_by.full_name', read_only=True, allow_null=True
    )
    # Use SerializerMethodField to generate fresh SAS tokens for Azure Blob Storage
    delivery_photo_1 = serializers.SerializerMethodField()
    delivery_photo_2 = serializers.SerializerMethodField()
    signature_image = serializers.SerializerMethodField()

    class Meta:
        model = UniformDeliveryDetail
        fields = [
            'id', 'is_delivered', 'delivered_at', 'delivered_by',
            'delivered_by_name', 'delivery_photo_1', 'delivery_photo_2',
            'signature_image', 'delivery_location', 'delivery_notes', 'items'
        ]
        read_only_fields = ['id', 'is_delivered', 'delivered_at', 'delivered_by']

    def get_delivery_photo_1(self, obj):
        """Genera URL con SAS token fresco para foto 1"""
        from apps.core.azure_utils import get_photo_url_with_sas
        return get_photo_url_with_sas(obj.delivery_photo_1)

    def get_delivery_photo_2(self, obj):
        """Genera URL con SAS token fresco para foto 2"""
        from apps.core.azure_utils import get_photo_url_with_sas
        return get_photo_url_with_sas(obj.delivery_photo_2)

    def get_signature_image(self, obj):
        """Genera URL con SAS token fresco para firma"""
        from apps.core.azure_utils import get_photo_url_with_sas
        return get_photo_url_with_sas(obj.signature_image)


class UniformItemCreateSerializer(serializers.Serializer):
    """Serializer para crear item de uniforme"""
    material = serializers.IntegerField(required=False, allow_null=True)
    item_type = serializers.ChoiceField(
        choices=UniformItem.ItemType.choices, required=False, allow_blank=True
    )
    custom_description = serializers.CharField(required=False, allow_blank=True)
    size = serializers.ChoiceField(
        choices=UniformItem.Size.choices, default=UniformItem.Size.NA
    )
    color = serializers.CharField(required=False, allow_blank=True)
    quantity = serializers.IntegerField(default=1, min_value=1)
    requires_return = serializers.BooleanField(default=False)
    return_date = serializers.DateField(required=False)

    def validate(self, data):
        if not data.get('material') and not data.get('item_type'):
            raise serializers.ValidationError(
                'Debe especificar material o tipo de prenda.'
            )
        if data.get('material'):
            try:
                material_obj = Material.objects.get(id=data['material'])
                if not data.get('custom_description'):
                    data['custom_description'] = material_obj.name
            except Material.DoesNotExist:
                raise serializers.ValidationError({'material': 'Material no encontrado.'})
        return data


class UniformDeliveryDetailCreateSerializer(serializers.Serializer):
    """Serializer para crear entrega de uniforme"""
    delivery_location = serializers.CharField(required=False, allow_blank=True)
    delivery_notes = serializers.CharField(required=False, allow_blank=True)
    items = UniformItemCreateSerializer(many=True)

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError('Debe incluir al menos un item.')
        return value


# ============ SUBSTITUTION ============

class SubstitutionDetailSerializer(serializers.ModelSerializer):
    substituted_personnel_name = serializers.CharField(
        source='substituted_personnel.get_full_name', read_only=True
    )
    substituted_personnel_code = serializers.CharField(
        source='substituted_personnel.employee_code', read_only=True
    )
    reason_display = serializers.CharField(
        source='get_reason_display', read_only=True
    )
    total_days = serializers.IntegerField(read_only=True)

    class Meta:
        model = SubstitutionDetail
        fields = [
            'id', 'substituted_personnel', 'substituted_personnel_name',
            'substituted_personnel_code', 'reason', 'reason_display',
            'reason_detail', 'assumed_functions', 'start_date', 'end_date',
            'specific_schedule', 'additional_compensation', 'compensation_notes',
            'total_days'
        ]
        read_only_fields = ['id', 'total_days']


class SubstitutionDetailCreateSerializer(serializers.Serializer):
    """Serializer para crear sustitución"""
    substituted_personnel = serializers.IntegerField()
    reason = serializers.ChoiceField(choices=SubstitutionDetail.SubstitutionReason.choices)
    reason_detail = serializers.CharField(required=False, allow_blank=True)
    assumed_functions = serializers.CharField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    specific_schedule = serializers.CharField(required=False, allow_blank=True)
    additional_compensation = serializers.BooleanField(default=False)
    compensation_notes = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        if data['start_date'] > data['end_date']:
            raise serializers.ValidationError(
                'start_date debe ser anterior a end_date.'
            )
        return data


# ============ RATE CHANGE ============

class RateChangeDetailSerializer(serializers.ModelSerializer):
    reason_display = serializers.CharField(
        source='get_reason_display', read_only=True
    )
    rate_difference = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    rate_percentage_change = serializers.FloatField(read_only=True)

    class Meta:
        model = RateChangeDetail
        fields = [
            'id', 'reason', 'reason_display', 'reason_detail',
            'current_rate', 'new_rate', 'rate_type',
            'start_date', 'end_date', 'additional_functions',
            'rate_difference', 'rate_percentage_change'
        ]
        read_only_fields = ['id', 'rate_difference', 'rate_percentage_change']


class RateChangeDetailCreateSerializer(serializers.Serializer):
    """Serializer para crear cambio de tasa"""
    reason = serializers.ChoiceField(choices=RateChangeDetail.ChangeReason.choices)
    reason_detail = serializers.CharField(required=False, allow_blank=True)
    current_rate = serializers.DecimalField(max_digits=10, decimal_places=2)
    new_rate = serializers.DecimalField(max_digits=10, decimal_places=2)
    rate_type = serializers.CharField(default='Horaria')
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    additional_functions = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        if data['start_date'] > data['end_date']:
            raise serializers.ValidationError(
                'start_date debe ser anterior a end_date.'
            )
        if data['new_rate'] == data['current_rate']:
            raise serializers.ValidationError(
                'La nueva tasa debe ser diferente a la actual.'
            )
        return data


# ============ OVERTIME ============

class OvertimeDetailSerializer(serializers.ModelSerializer):
    overtime_type_display = serializers.CharField(
        source='get_overtime_type_display', read_only=True
    )
    reason_display = serializers.CharField(
        source='get_reason_display', read_only=True
    )
    overtime_type_model_name = serializers.CharField(
        source='overtime_type_model.name', read_only=True, default=None
    )
    reason_model_name = serializers.CharField(
        source='reason_model.name', read_only=True, default=None
    )
    estimated_pay = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )

    class Meta:
        model = OvertimeDetail
        fields = [
            'id', 'overtime_type', 'overtime_type_display',
            'overtime_type_model', 'overtime_type_model_name',
            'reason', 'reason_display',
            'reason_model', 'reason_model_name',
            'reason_detail',
            'overtime_date', 'start_time', 'end_time', 'total_hours',
            'pay_multiplier', 'assigned_task',
            'was_completed', 'actual_start_time', 'actual_end_time',
            'actual_hours', 'completion_notes', 'estimated_pay'
        ]
        read_only_fields = ['id', 'total_hours', 'estimated_pay']


class OvertimeDetailCreateSerializer(serializers.Serializer):
    """Serializer para crear horas extra"""
    overtime_type = serializers.ChoiceField(
        choices=OvertimeDetail.OvertimeType.choices,
        default=OvertimeDetail.OvertimeType.REGULAR,
        required=False,
    )
    overtime_type_model = serializers.PrimaryKeyRelatedField(
        queryset=OvertimeTypeModel.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )
    reason = serializers.ChoiceField(
        choices=OvertimeDetail.OvertimeReason.choices,
        required=False,
    )
    reason_model = serializers.PrimaryKeyRelatedField(
        queryset=OvertimeReasonModel.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )
    reason_detail = serializers.CharField(required=False, allow_blank=True)
    overtime_date = serializers.DateField()
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    pay_multiplier = serializers.DecimalField(
        max_digits=3, decimal_places=2, default=1.5
    )
    assigned_task = serializers.CharField(required=False, allow_blank=True)


# ============ SHIFT CHANGE ============

class ShiftChangeDetailSerializer(serializers.ModelSerializer):
    reason_display = serializers.CharField(
        source='get_reason_display', read_only=True
    )
    exchange_with_name = serializers.CharField(
        source='exchange_with.get_full_name', read_only=True
    )
    is_exchange = serializers.BooleanField(read_only=True)

    class Meta:
        model = ShiftChangeDetail
        fields = [
            'id', 'reason', 'reason_display', 'reason_detail',
            'current_shift_name', 'current_shift_start', 'current_shift_end',
            'new_shift_name', 'new_shift_start', 'new_shift_end',
            'change_date', 'is_permanent', 'end_date',
            'exchange_with', 'exchange_with_name', 'exchange_confirmed',
            'is_exchange'
        ]
        read_only_fields = ['id', 'is_exchange']


class ShiftChangeDetailCreateSerializer(serializers.Serializer):
    """Serializer para crear cambio de turno"""
    reason = serializers.ChoiceField(choices=ShiftChangeDetail.ChangeReason.choices)
    reason_detail = serializers.CharField(required=False, allow_blank=True)
    current_shift_name = serializers.CharField(max_length=100)
    current_shift_start = serializers.TimeField()
    current_shift_end = serializers.TimeField()
    new_shift_name = serializers.CharField(max_length=100)
    new_shift_start = serializers.TimeField()
    new_shift_end = serializers.TimeField()
    change_date = serializers.DateField()
    is_permanent = serializers.BooleanField(default=False)
    end_date = serializers.DateField(required=False)
    exchange_with = serializers.IntegerField(required=False)

    def validate(self, data):
        if not data.get('is_permanent') and not data.get('end_date'):
            raise serializers.ValidationError(
                'end_date es requerido para cambios temporales.'
            )
        return data
