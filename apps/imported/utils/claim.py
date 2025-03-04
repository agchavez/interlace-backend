# utils/reclamos_utils.py

from typing import Optional, List
from django.core.files import File
from django.conf import settings

# Supongamos que tienes estos modelos (ajusta import según tu estructura real):

from django.contrib.auth import get_user_model

from apps.document.models.document import DocumentModel
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
def add_reclamo_log(reclamo: ClaimModel, old_state: str, new_state: str, changed_by: Optional[User] = None):
    """
    Placeholder para guardar en un modelo de logs (o en la tabla de historial de estados).
    """
    pass


# 3) Función para crear documentos (cuando suben archivos)
def create_documento(file_obj: File, name: Optional[str] = None) -> DocumentModel:
    """
    Crea un DocumentoModel usando el File subido (sube a Azure).
    """
    doc = DocumentModel(name=name if name else file_obj.name)
    doc.file = file_obj
    # Podrías extraer extension, content_type, etc. si gustas
    doc.save()
    return doc


# 4) Función para crear un reclamo con sus 4 documentos
def create_reclamo(
    tracker_id: int,
    assigned_user_id: Optional[int],
    tipo: str,
    descripcion: str,
    doc_trailer_file: Optional[File],
    doc_descarga_file: Optional[File],
    doc_contenido_file: Optional[File],
    doc_producto_file: Optional[File]
) -> ClaimModel:
    """
    Crea un ReclamoModel, registra los documentos (si existen) y
    retorna el reclamo creado.
    Luego, podría enviar notificación/correo a assigned_user_id,
    o lo que se requiera.
    """
    tracker = TrackerModel.objects.get(pk=tracker_id)

    assigned_user = None
    if assigned_user_id:
        assigned_user = User.objects.get(pk=assigned_user_id)

    # 1. Creamos reclamo
    reclamo = ClaimModel.objects.create(
        tracker=tracker,
        assigned_to=assigned_user,
        tipo=tipo,
        descripcion=descripcion,
        status="PENDIENTE"
    )

    # 2. Creamos los documentos (si se subieron archivos) y asignamos
    if doc_trailer_file:
        doc_trailer = create_documento(doc_trailer_file, name="Foto del Tráiler")
        reclamo.doc_trailer = doc_trailer

    if doc_descarga_file:
        doc_descarga = create_documento(doc_descarga_file, name="Foto de la Descarga")
        reclamo.doc_descarga = doc_descarga

    if doc_contenido_file:
        doc_contenido = create_documento(doc_contenido_file, name="Foto del Contenido")
        reclamo.doc_contenido = doc_contenido

    if doc_producto_file:
        doc_producto = create_documento(doc_producto_file, name="Foto del Producto")
        reclamo.doc_producto = doc_producto

    reclamo.save()

    # 3. Opcional: Enviar notificación/correo
    if assigned_user:
        send_notification(
            user=assigned_user,
            title=f"Nuevo reclamo #{reclamo.id}",
            description=f"Se te ha asignado un reclamo de tipo {tipo}"
        )
        send_email(
            user=assigned_user,
            subject=f"Reclamo #{reclamo.id} asignado",
            message=f"Reclamo de tipo {tipo}, descripción: {descripcion}."
        )

    return reclamo


# 5) Función para cambiar estado de un reclamo
def change_reclamo_state(
    reclamo_id: int,
    new_state: str,
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
    add_reclamo_log(reclamo, old_state, new_state, changed_by)

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
