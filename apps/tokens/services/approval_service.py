"""
Servicio para determinar niveles de aprobación de tokens.

Define la lógica de:
- Cuántos niveles de aprobación requiere cada tipo de token
- Quién puede aprobar según la jerarquía del beneficiario
- Auto-aprobación para jerarquías superiores
"""
from apps.personnel.models import PersonnelProfile


class ApprovalLevelService:
    """
    Servicio para determinar niveles de aprobación de tokens.

    Tipos de tokens y sus niveles:
    - UN nivel: PERMIT_HOUR, PERMIT_DAY, OVERTIME, EXIT_PASS
      - Operativo → Supervisor (L1)
      - Supervisor → Jefe de Área (L2)
      - Jefe de Área → Gerente (L3)

    - DOS niveles: SUBSTITUTION, RATE_CHANGE, SHIFT_CHANGE
      - Solo para operativos
      - Supervisor (L1) + Jefe de Área (L2)

    - SIN aprobación: UNIFORM_DELIVERY
    """

    # Tokens de UN nivel (según jerarquía del beneficiario)
    SINGLE_LEVEL_TYPES = [
        'PERMIT_HOUR',
        'PERMIT_DAY',
        'OVERTIME',
        'EXIT_PASS',
    ]

    # Tokens de DOS niveles (solo operativos)
    TWO_LEVEL_TYPES = [
        'SUBSTITUTION',
        'RATE_CHANGE',
        'SHIFT_CHANGE',
    ]

    # Sin aprobación
    NO_APPROVAL_TYPES = [
        'UNIFORM_DELIVERY',
    ]

    # Orden de jerarquía
    HIERARCHY_ORDER = {
        PersonnelProfile.OPERATIVE: 0,
        PersonnelProfile.SUPERVISOR: 1,
        PersonnelProfile.AREA_MANAGER: 2,
        PersonnelProfile.CD_MANAGER: 3,
    }

    @classmethod
    def determine_approval_levels(cls, token_type, beneficiary_hierarchy=None, is_external=False):
        """
        Determina los niveles de aprobación requeridos.

        Args:
            token_type: Tipo de token (PERMIT_HOUR, etc.)
            beneficiary_hierarchy: Nivel jerárquico del beneficiario (OPERATIVE, SUPERVISOR, etc.)
            is_external: Si es para persona externa (pases de salida)

        Returns:
            tuple: (requires_l1, requires_l2, requires_l3, initial_status)
        """
        from apps.tokens.models import TokenRequest

        # Sin aprobación
        if token_type in cls.NO_APPROVAL_TYPES:
            return (False, False, False, TokenRequest.Status.APPROVED)

        # Pase de salida para externos: L1 + L2
        if token_type == 'EXIT_PASS' and is_external:
            return (True, True, False, TokenRequest.Status.PENDING_L1)

        # Tokens de dos niveles (solo operativos)
        if token_type in cls.TWO_LEVEL_TYPES:
            if beneficiary_hierarchy and beneficiary_hierarchy != PersonnelProfile.OPERATIVE:
                raise ValueError(
                    f"El tipo de token {token_type} solo está permitido para personal operativo"
                )
            return (True, True, False, TokenRequest.Status.PENDING_L1)

        # Tokens de un nivel (según jerarquía del beneficiario)
        if token_type in cls.SINGLE_LEVEL_TYPES:
            if not beneficiary_hierarchy:
                # Sin beneficiario definido, usar nivel mínimo
                return (True, False, False, TokenRequest.Status.PENDING_L1)

            if beneficiary_hierarchy == PersonnelProfile.OPERATIVE:
                # Operativo → lo aprueba Supervisor (L1)
                return (True, False, False, TokenRequest.Status.PENDING_L1)
            elif beneficiary_hierarchy == PersonnelProfile.SUPERVISOR:
                # Supervisor → lo aprueba Jefe de Área (L2)
                return (False, True, False, TokenRequest.Status.PENDING_L2)
            elif beneficiary_hierarchy == PersonnelProfile.AREA_MANAGER:
                # Jefe de Área → lo aprueba Gerente (L3)
                return (False, False, True, TokenRequest.Status.PENDING_L3)
            else:  # CD_MANAGER
                # Gerente → auto-aprobado
                return (False, False, False, TokenRequest.Status.APPROVED)

        # Por defecto (fallback)
        return (True, True, False, TokenRequest.Status.PENDING_L1)

    @classmethod
    def can_auto_approve(cls, requester_profile, beneficiary_profile):
        """
        Determina si el solicitante puede auto-aprobar el token.

        Reglas:
        - Solicitante debe tener jerarquía >= AREA_MANAGER
        - Beneficiario debe tener jerarquía inferior al solicitante
        - No puede ser el mismo usuario
        - Gerente puede aprobar todo

        Args:
            requester_profile: PersonnelProfile del solicitante
            beneficiary_profile: PersonnelProfile del beneficiario

        Returns:
            bool: True si puede auto-aprobar
        """
        if not requester_profile or not beneficiary_profile:
            return False

        # No puede auto-aprobar su propio token
        if requester_profile.id == beneficiary_profile.id:
            return False

        requester_level = cls.HIERARCHY_ORDER.get(requester_profile.hierarchy_level, 0)
        beneficiary_level = cls.HIERARCHY_ORDER.get(beneficiary_profile.hierarchy_level, 0)

        # Solo jefes de área y gerentes pueden auto-aprobar
        if requester_level < cls.HIERARCHY_ORDER[PersonnelProfile.AREA_MANAGER]:
            return False

        # Debe tener jerarquía estrictamente superior al beneficiario
        return requester_level > beneficiary_level

    @classmethod
    def get_approver_hierarchy_for_level(cls, level):
        """
        Retorna la jerarquía mínima necesaria para aprobar un nivel.

        Args:
            level: Nivel de aprobación (1, 2, o 3)

        Returns:
            str: Constante de jerarquía (SUPERVISOR, AREA_MANAGER, CD_MANAGER)
        """
        hierarchy_for_level = {
            1: PersonnelProfile.SUPERVISOR,
            2: PersonnelProfile.AREA_MANAGER,
            3: PersonnelProfile.CD_MANAGER,
        }
        return hierarchy_for_level.get(level)

    @classmethod
    def can_approve_level(cls, approver_profile, beneficiary_profile, level):
        """
        Verifica si un aprobador puede aprobar un token en un nivel específico.

        Args:
            approver_profile: PersonnelProfile del aprobador
            beneficiary_profile: PersonnelProfile del beneficiario (puede ser None)
            level: Nivel de aprobación (1, 2, o 3)

        Returns:
            bool: True si puede aprobar
        """
        if not approver_profile:
            return False

        approver_level = cls.HIERARCHY_ORDER.get(approver_profile.hierarchy_level, 0)

        # Gerente puede aprobar cualquier nivel
        if approver_profile.hierarchy_level == PersonnelProfile.CD_MANAGER:
            return True

        # Si hay beneficiario, el aprobador debe tener jerarquía superior
        if beneficiary_profile:
            beneficiary_level = cls.HIERARCHY_ORDER.get(beneficiary_profile.hierarchy_level, 0)
            if approver_level <= beneficiary_level:
                return False

        # Verificar jerarquía mínima para el nivel
        required_hierarchy = cls.get_approver_hierarchy_for_level(level)
        if not required_hierarchy:
            return False

        required_level = cls.HIERARCHY_ORDER.get(required_hierarchy, 0)
        return approver_level >= required_level

    @classmethod
    def is_token_type_allowed_for_hierarchy(cls, token_type, beneficiary_hierarchy):
        """
        Verifica si un tipo de token está permitido para una jerarquía.

        Args:
            token_type: Tipo de token
            beneficiary_hierarchy: Jerarquía del beneficiario

        Returns:
            bool: True si está permitido
        """
        # Tokens de dos niveles solo para operativos
        if token_type in cls.TWO_LEVEL_TYPES:
            return beneficiary_hierarchy == PersonnelProfile.OPERATIVE

        # Resto de tokens permitidos para todos
        return True
