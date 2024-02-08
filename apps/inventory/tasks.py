import datetime

from .models import InventoryMovementModel
from apps.tracker.models import TrackerDetailProductModel
from django.db import transaction
from celery import shared_task


# Movimientos de inventario aplicados a los Inventario

@shared_task
@transaction.atomic
def apply_inventory_movements():
    products = []
    # Obtener los movimientos de inventario que no han sido aplicados
    inventory_movements = InventoryMovementModel.objects.filter(is_applied=False)
    if not inventory_movements:
        return 'No hay movimientos de inventario para aplicar'
    # Recorrer los movimientos de inventario
    for inventory_movement in inventory_movements:
        # obtener o crear el inventario
        tracker_detail_product = inventory_movement.tracker_detail_product
        # Actualizar el inventario
        inventory_movement.initial_quantity = tracker_detail_product.available_quantity
        tracker_detail_product.available_quantity = tracker_detail_product.available_quantity + inventory_movement.quantity
        tracker_detail_product.save()
        inventory_movement.is_applied = True
        inventory_movement.applied_date = datetime.datetime.now()
        inventory_movement.save()
        products.append({
            'product': str(tracker_detail_product),
            'quantity': inventory_movement.quantity,
            'available_quantity': tracker_detail_product.available_quantity
        })

    return products

