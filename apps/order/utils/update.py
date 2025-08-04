from django.db import transaction
from rest_framework import serializers, status

from ..exceptions.order_detail import CustomAPIException
from ..models.detail import OrderDetailModel
from ..models.history import OrderHistoryModel
from apps.tracker.models import TrackerDetailOutputModel


# Validar y actualizar los detalles de la orden y bajar la cantidad disponible en los TRACKINGS y almancenar el log

def validate_and_update_order_detail(order, tracker):
    # No se puede actualizar una orden que no esta en estado COMPLETED
    if order.status == 'COMPLETE':
        raise CustomAPIException(
            detail="No se puede actualizar una orden que no esta en estado Completado",
            code='order_not_completed',
        )
    
    # FUNCIONALIDAD HÍBRIDA: Solo procesar order_details que tienen tracker_detail_product
    # Los productos directos (product != null, tracker_detail_product = null) no se procesan aquí
    order_details = OrderDetailModel.objects.filter(
        order=order, 
        tracker_detail_product__isnull=False
    ).select_related('tracker_detail_product')
    
    tracker_detail_product_list = TrackerDetailOutputModel.objects.filter(tracker=tracker).select_related(
        'tracker_detail_product__tracker_detail__product')

    for tracker_out_detail in tracker_detail_product_list:
        try:
            order_detail = order_details.get(tracker_detail_product=tracker_out_detail.tracker_detail_product)
        except OrderDetailModel.DoesNotExist:
            # FUNCIONALIDAD HÍBRIDA: Si el producto del tracker no está en la orden como producto con tracker,
            # simplemente lo ignoramos. Solo procesamos productos que tienen tracker_detail_product en la orden.
            # Los productos directos en la orden no se procesan al completar trackers.
            continue

        quantity_available_order = order_detail.quantity_available

        if tracker_out_detail.quantity > quantity_available_order:
            procto_name = tracker_out_detail.tracker_detail_product.tracker_detail.product.name
            raise CustomAPIException(
                detail=f"El producto de salida {procto_name}, supera el stock disponible en la orden",
                code='quantity_order_detail_exceeded',
            )

    return True


# Actualizar los detalles de la orden y bajar la cantidad disponible en los TRACKINGS y almancenar el log
@transaction.atomic
def update_order_detail(order, tracker):
    # FUNCIONALIDAD HÍBRIDA: Solo procesar order_details que tienen tracker_detail_product
    # Los productos directos (product != null, tracker_detail_product = null) no se procesan aquí
    order_details_with_tracker = OrderDetailModel.objects.filter(
        order=order, 
        tracker_detail_product__isnull=False
    ).select_related('tracker_detail_product')
    
    # Obtener TODOS los order_details para verificar el estado final de la orden
    all_order_details = OrderDetailModel.objects.filter(order=order)
    
    tracker_detail_product_list = TrackerDetailOutputModel.objects.filter(tracker=tracker).select_related(
        'tracker_detail_product__tracker_detail__product')

    for order_detail in order_details_with_tracker:
        # Solo procesar si el order_detail tiene tracker_detail_product
        if order_detail.tracker_detail_product is None:
            continue

        # actualizar la cantidad disponible
        tracker_detail_product = tracker_detail_product_list.filter(
            tracker_detail_product=order_detail.tracker_detail_product)

        if not tracker_detail_product.exists():
            continue

        tracker_detail_product = tracker_detail_product.first()

        order_detail.quantity_available = order_detail.quantity_available - tracker_detail_product.quantity

        # guardar el detalle de la orden
        order_detail.save()
        # crear el log
        order_history = OrderHistoryModel.objects.create(
            order_detail=order_detail,
            tracker=tracker,
            quantity=tracker_detail_product.quantity,
        )
        order_history.save()

    # La orden cambia a estado de IN_PROCESS
    if order.status == 'PENDING':
        order.status = 'IN_PROCESS'
        order.save()

    # FUNCIONALIDAD HÍBRIDA: Verificar si todas las cantidades están en 0 (incluyendo productos directos)
    # Solo los productos con tracker_detail_product pueden ser procesados por trackers
    # Los productos directos siempre mantienen su quantity_available original
    if all_order_details.filter(
        tracker_detail_product__isnull=False,
        quantity_available__gt=0
    ).count() == 0:
        order.status = 'COMPLETED'
        order.save()

    # si todo esta bien retornar true
    return True
