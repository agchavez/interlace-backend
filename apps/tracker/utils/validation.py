from django.db.models import Sum

from apps.tracker.exceptions.tracker import TrackerCompleted, UserWithoutDistributorCenter, \
    InputDocumentNumberRegistered, InputDocumentNumberIsNotNumber, QuantityRequired, \
    TrackerCompletedDetailRequired, InputDocumentNumberRequired, OutputDocumentNumberRequired, TransferNumberRequired, \
    OperatorRequired, OutputTypeRequired, InvoiceRequired, ContainerNumberRequired, PlateNumberRequired, DriverRequired, \
    OriginLocationRequired

from ..models import TrackerModel, TrackerDetailProductModel


def validate_create_tracker(request, id=None):
    usuario = request.user
    distribuidor = usuario.centro_distribucion
    data = request.data
    instance = None
    if id is not None:
        instance = TrackerModel.objects.filter(id=id).first()

    # Validar si el documento de entrada ya esta registrado
    if data.get('input_document_number') and instance:
        if TrackerModel.objects.filter(input_document_number=data.get('input_document_number')).exclude(
                id=instance.id).exists():
            raise InputDocumentNumberRegistered()
        # El documento de entrada no debe ser numerico en el caso que lo mande
        if not data.get('input_document_number').isnumeric():
            raise InputDocumentNumberIsNotNumber()

    # Validaciones de documento de salida
    if data.get('output_document_number') and instance:
        if TrackerModel.objects.filter(output_document_number=data.get('output_document_number')).exclude(
                id=instance.id).exists():
            raise InputDocumentNumberRegistered()
        # El documento de salida no debe ser numerico en el caso que lo mande
        if not data.get('output_document_number').isnumeric():
            raise InputDocumentNumberIsNotNumber()

    # Validaciones de numero de traslado
    if data.get('transfer_number') and instance:
        if TrackerModel.objects.filter(transfer_number=data.get('transfer_number')).exclude(
                id=instance.id).exists():
            raise InputDocumentNumberRegistered()
        # El numero de traslado no debe ser numerico en el caso que lo mande
        if not data.get('transfer_number').isnumeric():
            raise InputDocumentNumberIsNotNumber()

    # Validacion de contabilzado
    if data.get('accounted') and instance:
        if not data.get('accounted').isnumeric():
            raise InputDocumentNumberIsNotNumber()

    # Vlidar centro de distribucion del usuario
    if distribuidor is None:
        raise UserWithoutDistributorCenter()
    return (usuario, distribuidor)


# Validaciones para marcar completado un tracker
def validate_complete_tracker(tracker):
    # Si ya esta completado, no se puede completar de nuevo
    if tracker.status == 'COMPLETE':
        raise TrackerCompleted()
    # Debe exister almenos un detalle de tracker
    if tracker.tracker_detail.count() == 0:
        raise TrackerCompletedDetailRequired()

    # la localidad de origen es requerida
    if not tracker.origin_location:
        raise OriginLocationRequired()

    if tracker.type == 'LOCAL':
        # Validar numero de entrada, salida y traslado
        if not tracker.input_document_number:
            raise InputDocumentNumberRequired()
        if not tracker.output_document_number:
            raise OutputDocumentNumberRequired()
        if not tracker.transfer_number:
            raise TransferNumberRequired()
        if not tracker.driver:
            raise DriverRequired()

        # Validar la data del oeperador y las fechas de entrada y salida
        if not tracker.operator_1 or not tracker.input_date or not tracker.output_date:
            raise OperatorRequired()

        # Validaciones para el tipo de salida del producto
        if not tracker.output_type:
            raise OutputTypeRequired()
    if tracker.type == 'IMPORT':
        # Validar numero de factura y numero de contenedor
        if not tracker.invoice_number:
            raise InvoiceRequired()
        if not tracker.container_number:
            raise ContainerNumberRequired()
        if not tracker.driver_import:
            raise DriverRequired()
    # validar numero de placa y driver
    if not tracker.plate_number:
        raise PlateNumberRequired()

    # Validar que todos los detalles de tracker tengan la cantidad completa
    for tracker_detail in tracker.tracker_detail.all():
        sum_quantity = TrackerDetailProductModel.objects.filter(tracker_detail=tracker_detail).aggregate(
            Sum('quantity'))
        if sum_quantity.get('quantity__sum') != tracker_detail.quantity:
            raise QuantityRequired()
    return True
