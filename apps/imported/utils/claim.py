# utils/reclamos_utils.py

from typing import Optional, List
from django.core.files import File
from django.conf import settings

# Supongamos que tienes estos modelos (ajusta import según tu estructura real):

from django.contrib.auth import get_user_model

from apps.document.models.document import DocumentModel
from apps.document.utils.documents import create_documento
from apps.imported.model.claim import ClaimModel
from apps.tracker.models import TrackerModel

User = get_user_model()

# 1) Funciones para notificaciones y correos
def send_notification(user: User, title: str, description: str):
    """
    Placeholder para crear un registro de notificación en la BD.
    """
    pass

def send_email(user: User, subject: str, message: str):
    """
    Placeholder para el envío de correos (por ejemplo, usando django.core.mail.send_mail).
    """
    if not user.email:
        return
    # Podrías usar send_mail, o un backend distinto
    # from django.core.mail import send_mail
    # send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=True)
    print(f"Enviando correo a {user.email}: {subject}\n{message}")


# 2) Función para registrar logs de cambios (historial)
def add_reclamo_log(reclamo: ClaimModel, old_state: str, new_state: str, changed_by: Optional[User] = None, observations: Optional[str] = None):
    """
    Placeholder para guardar en un modelo de logs (o en la tabla de historial de estados).
    """
    pass

def create_reclamo(
        tracker_id: int,
        assigned_user_id: Optional[int],
        claim_type: str,
        description: str,
        claim_number: Optional[str] = None,
        discard_doc: Optional[str] = None,
        observations: Optional[str] = None,
        claim_file: Optional[File] = None,
        credit_memo_file: Optional[File] = None,
        observations_file: Optional[File] = None,
        photo_files: Optional[dict] = None
    ) -> ClaimModel:
        """
        Crea un ClaimModel con todos los campos necesarios y adjunta los documentos.

        Args:
            tracker_id: ID del tracker asociado
            assigned_user_id: ID del usuario asignado (opcional)
            claim_type: Tipo de reclamo (FALTANTE, SOBRANTE, DAÑOS_CALIDAD_TRANSPORTE)
            description: Descripción del reclamo
            claim_number: Número de claim (opcional)
            discard_doc: Documento de descarte (opcional)
            observations: Observaciones adicionales (opcional)
            claim_file: Archivo del claim (opcional)
            credit_memo_file: Archivo de nota de crédito (opcional)
            observations_file: Archivo de observaciones (opcional)
            photo_files: Diccionario con listas de archivos por categoría
        """
        tracker = TrackerModel.objects.get(pk=tracker_id)

        assigned_user = None
        if assigned_user_id:
            assigned_user = User.objects.get(pk=assigned_user_id)

        # 1. Creamos reclamo con todos los campos
        reclamo = ClaimModel.objects.create(
            tracker=tracker,
            assigned_to=assigned_user,
            claim_type=claim_type,
            description=description,
            status="PENDIENTE",
            claim_number=claim_number,
            discard_doc=discard_doc,
            observations=observations
        )

        # 2. Añadimos los archivos de documentos principales
        if claim_file:
            # En lugar de asignar directamente, usar create_documento()
            doc_claim = create_documento(claim_file,"Document Claim",  "Claim", reclamo.claim_code)
            reclamo.claim_file = doc_claim.file

        if credit_memo_file:
            doc_credit = create_documento(credit_memo_file, "Credit Memo", "Claim", reclamo.claim_code)
            reclamo.credit_memo_file = doc_credit.file

        if observations_file:
            doc_obs = create_documento(observations_file, "Observations", "Claim", reclamo.claim_code)
            reclamo.observations_file = doc_obs.file

        reclamo.save()

        # 3. Procesamos los archivos de fotos por categoría
        if photo_files:
            # Mapeo de nombres de campo a relaciones ManyToMany
            photo_fields = {
                "photos_container_closed": reclamo.photos_container_closed,
                "photos_container_one_open": reclamo.photos_container_one_open,
                "photos_container_two_open": reclamo.photos_container_two_open,
                "photos_container_top": reclamo.photos_container_top,
                "photos_during_unload": reclamo.photos_during_unload,
                "photos_pallet_damage": reclamo.photos_pallet_damage,
                "photos_damaged_product_base": reclamo.photos_damaged_product_base,
                "photos_damaged_product_dents": reclamo.photos_damaged_product_dents,
                "photos_damaged_boxes": reclamo.photos_damaged_boxes,
                "photos_grouped_bad_product": reclamo.photos_grouped_bad_product,
                "photos_repalletized": reclamo.photos_repalletized
            }

            # Para cada categoría de fotos
            for field_name, file_list in photo_files.items():
                if field_name in photo_fields and file_list:
                    # Nombres descriptivos según la categoría
                    field_descriptions = {
                        "photos_container_closed": "Contenedor cerrado",
                        "photos_container_one_open": "Contenedor con 1 puerta abierta",
                        "photos_container_two_open": "Contenedor con 2 puertas abiertas",
                        "photos_container_top": "Vista superior del contenedor",
                        "photos_during_unload": "Durante la descarga",
                        "photos_pallet_damage": "Daños en pallets",
                        "photos_damaged_product_base": "Base de producto dañado",
                        "photos_damaged_product_dents": "Abolladuras en producto",
                        "photos_damaged_boxes": "Cajas dañadas",
                        "photos_grouped_bad_product": "Producto en mal estado agrupado",
                        "photos_repalletized": "Producto repaletizado"
                    }

                    # Descripción para el documento
                    desc = field_descriptions.get(field_name, field_name)

                    # Creamos un documento para cada archivo y lo añadimos a la relación
                    for i, file_obj in enumerate(file_list):
                        doc = create_documento(file_obj, name=f"{desc} #{i+1}", folder="Claim", subfolder=reclamo.claim_code)
                        photo_fields[field_name].add(doc)

        # 4. Enviar notificación/correo si hay un usuario asignado
        if assigned_user:
            send_notification(
                user=assigned_user,
                title=f"Nuevo reclamo #{reclamo.id}",
                description=f"Se te ha asignado un reclamo de tipo {claim_type}"
            )
            send_email(
                user=assigned_user,
                subject=f"Reclamo #{reclamo.id} asignado",
                message=f"Reclamo de tipo {claim_type}, descripción: {description}."
            )

        return reclamo


# 5) Función para cambiar estado de un reclamo
def change_reclamo_state(
    reclamo_id: int,
    new_state: str,
    observations: Optional[str] = None,
    changed_by_id: Optional[int] = None,
    send_notifications: bool = True
) -> ClaimModel:
    """
    Cambia el estado de un reclamo, registra logs y (opcionalmente)
    envía notificaciones/correos.
    """
    reclamo = ClaimModel.objects.get(pk=reclamo_id)
    old_state = reclamo.status

    # Actualizamos
    reclamo.status = new_state
    reclamo.save()

    # Guardar log de cambios
    changed_by = User.objects.get(pk=changed_by_id) if changed_by_id else None
    add_reclamo_log(reclamo, old_state, new_state, changed_by, observations)

    # Notificar si corresponde
    if send_notifications and reclamo.assigned_to:
        send_notification(
            user=reclamo.assigned_to,
            title=f"Reclamo #{reclamo.id} cambió de estado",
            description=f"De {old_state} a {new_state}"
        )
        send_email(
            user=reclamo.assigned_to,
            subject=f"Reclamo #{reclamo.id} - Cambio de estado",
            message=f"El reclamo pasó de {old_state} a {new_state}."
        )

    return reclamo
