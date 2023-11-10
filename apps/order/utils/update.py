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
    order_details = OrderDetailModel.objects.filter(order=order).select_related('tracker_detail_product')
    tracker_detail_product_list = TrackerDetailOutputModel.objects.filter(tracker=tracker).select_related(
        'tracker_detail_product__tracker_detail__product')

    for tracker_out_detail in tracker_detail_product_list:
        try:
            order_detail = order_details.get(tracker_detail_product=tracker_out_detail.tracker_detail_product)
        except OrderDetailModel.DoesNotExist:
            raise serializers.ValidationError(f"El producto {tracker_out_detail.product.name} no está en la orden")

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
    order_details = OrderDetailModel.objects.filter(order=order).select_related('tracker_detail_product')
    tracker_detail_product_list = TrackerDetailOutputModel.objects.filter(tracker=tracker).select_related(
        'tracker_detail_product__tracker_detail__product')

    for order_detail in order_details:

        # actualizar la cantidad disponible
        tracker_detail_product = tracker_detail_product_list.get(
            tracker_detail_product=order_detail.tracker_detail_product)


        if not tracker_detail_product:
            continue

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

    # si todas las cantidades estan en 0 cambiar el estado de la orden a COMPLETE
    if order_details.filter(quantity_available__gt=0).count() == 0:
        order.status = 'COMPLETE'
        order.save()


    # si todo esta bien retornar true
    return True
