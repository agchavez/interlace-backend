"""
Vistas públicas para tokens (sin autenticación requerida)
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.http import HttpResponse

from ..models import TokenRequest
from ..serializers import PublicTokenSerializer
from ..utils import generate_token_pdf


@api_view(['GET'])
@permission_classes([AllowAny])
def public_token_detail(request, token_code):
    """
    Vista pública para ver el detalle de un token.
    Usada por operativos sin acceso al sistema para ver su QR.

    URL: /api/tokens/public/{token_code}/

    Acepta tanto UUID (token_code) como display_number (TK-2026-000001).
    Solo muestra información del token si está en estado válido
    (no muestra tokens rechazados, cancelados, etc.)
    """
    # Intentar buscar primero por display_number (formato TK-YYYY-NNNNNN)
    token = TokenRequest.objects.filter(display_number__iexact=token_code).first()

    # Si no se encuentra, buscar por token_code (UUID)
    if not token:
        token = TokenRequest.objects.filter(token_code=token_code).first()

    if not token:
        return Response(
            {'error': 'Token no encontrado.'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Solo mostrar tokens en estados válidos
    valid_statuses = [
        TokenRequest.Status.PENDING_L1,
        TokenRequest.Status.PENDING_L2,
        TokenRequest.Status.PENDING_L3,
        TokenRequest.Status.APPROVED,
        TokenRequest.Status.USED,  # También mostrar tokens usados para referencia
    ]

    if token.status not in valid_statuses:
        return Response(
            {'error': 'Este token no está disponible para visualización.'},
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = PublicTokenSerializer(token)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def public_token_by_code(request, display_number):
    """
    Vista pública para ver el detalle de un token por display_number.
    URL: /api/tokens/public/code/{display_number}/

    Alternativa usando específicamente display_number (TK-2026-000001).
    """
    token = get_object_or_404(TokenRequest, display_number__iexact=display_number)

    # Solo mostrar tokens en estados válidos
    valid_statuses = [
        TokenRequest.Status.PENDING_L1,
        TokenRequest.Status.PENDING_L2,
        TokenRequest.Status.PENDING_L3,
        TokenRequest.Status.APPROVED,
        TokenRequest.Status.USED,
    ]

    if token.status not in valid_statuses:
        return Response(
            {'error': 'Este token no está disponible para visualización.'},
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = PublicTokenSerializer(token)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def public_token_verify(request, token_code):
    """
    Vista pública rápida para verificar si un token es válido.
    URL: /api/tokens/public/verify/{token_code}/

    Devuelve información mínima para verificación rápida.
    Útil para personal de seguridad con acceso limitado.
    """
    # Intentar buscar primero por display_number (formato TK-YYYY-NNNNNN)
    token = TokenRequest.objects.filter(display_number__iexact=token_code).first()

    # Si no se encuentra, buscar por token_code (UUID)
    if not token:
        token = TokenRequest.objects.filter(token_code=token_code).first()

    if not token:
        return Response({
            'valid': False,
            'message': 'Token no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)

    # Verificar estado
    if token.status != TokenRequest.Status.APPROVED:
        return Response({
            'valid': False,
            'display_number': token.display_number,
            'status': token.status,
            'status_display': token.get_status_display(),
            'message': f'Token no está aprobado. Estado: {token.get_status_display()}'
        })

    # Verificar vigencia
    if not token.is_valid:
        return Response({
            'valid': False,
            'display_number': token.display_number,
            'status': token.status,
            'status_display': token.get_status_display(),
            'message': 'Token fuera del período de vigencia'
        })

    # Token válido
    return Response({
        'valid': True,
        'display_number': token.display_number,
        'token_type': token.token_type,
        'token_type_display': token.get_token_type_display(),
        'status': token.status,
        'status_display': token.get_status_display(),
        'personnel_name': token.personnel.full_name if token.personnel else None,
        'personnel_code': token.personnel.employee_code if token.personnel else None,
        'distributor_center': token.distributor_center.name if token.distributor_center else None,
        'valid_from': token.valid_from,
        'valid_until': token.valid_until,
        'message': 'Token válido para uso'
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def public_token_pdf(request, token_code):
    """
    Vista pública para descargar el PDF de un token.
    URL: /api/tokens/public/{token_code}/pdf/

    Acepta tanto UUID (token_code) como display_number (TK-2026-000001).
    Solo genera PDF para tokens en estados válidos.
    """
    # Intentar buscar primero por display_number
    token = TokenRequest.objects.filter(display_number__iexact=token_code).first()

    # Si no se encuentra, buscar por token_code (UUID)
    if not token:
        token = TokenRequest.objects.filter(token_code=token_code).first()

    if not token:
        return Response(
            {'error': 'Token no encontrado.'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Solo generar PDF para tokens en estados válidos
    valid_statuses = [
        TokenRequest.Status.PENDING_L1,
        TokenRequest.Status.PENDING_L2,
        TokenRequest.Status.PENDING_L3,
        TokenRequest.Status.APPROVED,
        TokenRequest.Status.USED,
    ]

    if token.status not in valid_statuses:
        return Response(
            {'error': 'Este token no está disponible para descarga.'},
            status=status.HTTP_404_NOT_FOUND
        )

    try:
        pdf_buffer = generate_token_pdf(token)
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="token_{token.display_number}.pdf"'
        return response
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error generando PDF público para token {token.id}: {e}")
        return Response(
            {'error': 'Error al generar el documento PDF'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
