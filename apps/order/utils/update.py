from django.db import transaction
from rest_framework import serializers

from ..models import OrderDetailModel, OrderHistoryModel
from apps.tracker.models import TrackerDetailProductModel


# Validar y actualizar los detalles de la orden y bajar la cantidad disponible en los TRACKINGS y almancenar el log

def validate_and_update_order_detail(order, tracker, quantity):
    # Lista de detalles de la orden
    order_details = OrderDetailModel.objects.filter(order=order)
    # Lista de productios en el tracker
    tracker_detail_product_list = TrackerDetailProductModel.objects.filter(tracker_detail__tracker=tracker)
    # validar que los productos esten en el tracker esten en la orden y que la cantidad este disponible
    for tracker_detail_product in tracker_detail_product_list:
        # validar que el producto este en la orden
        if tracker_detail_product.product not in order_details:
            # Lanzar error
            raise serializers.ValidationError(
                "El producto " + tracker_detail_product.product.name + " no esta en la orden")
        # validar que la cantidad este disponible
        if tracker_detail_product.quantity < quantity:
            # Lanzar error
            raise serializers.ValidationError(
                "El producto " + tracker_detail_product.product.name + " no tiene la cantidad disponible")

    # si todo esta bien retornar true
    return True


# Actualizar los detalles de la orden y bajar la cantidad disponible en los TRACKINGS y almancenar el log
@transaction.atomic
def update_order_detail(order, tracker, quantity):
    # Lista de detalles de la orden
    order_details = OrderDetailModel.objects.filter(order=order)
    # Lista de productios en el tracker
    tracker_detail_product_list = TrackerDetailProductModel.objects.filter(tracker_detail__tracker=tracker)
    # validar que los productos esten en el tracker esten en la orden y que la cantidad este disponible
    for tracker_detail_product in tracker_detail_product_list:
        # validar que el producto este en la orden
        if tracker_detail_product.product not in order_details:
            # Lanzar error
            raise serializers.ValidationError(
                "El producto " + tracker_detail_product.product.name + " no esta en la orden")
        # validar que la cantidad este disponible
        if tracker_detail_product.quantity < quantity:
            # Lanzar error
            raise serializers.ValidationError(
                "El producto " + tracker_detail_product.product.name + " no tiene la cantidad disponible")

        # actualizar la cantidad disponible
        tracker_detail_product.quantity = tracker_detail_product.quantity - quantity
        tracker_detail_product.save()

        # crear el log
        order_history = OrderHistoryModel.objects.create(
            order_detail=tracker_detail_product.tracker_detail,
            tracker=tracker,
            quantity=quantity
        )
        order_history.save()

    # si todas las cantidades estan en 0 cambiar el estado de la orden a COMPLETE
    if tracker_detail_product_list.filter(quantity__gt=0).count() == 0:
        order.status = 'COMPLETE'
        order.save()

    # si todo esta bien retornar true
    return True
