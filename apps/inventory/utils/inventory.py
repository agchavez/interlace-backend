# Funcion par actualizar el reajuste aplicar todo aquel producto que no se encuentre en el archivo
from celery import shared_task

from apps.inventory.models import InventoryMovementModel
from apps.tracker.models import TrackerDetailProductModel

@shared_task( name='update_adjustment_movement')
def update_adjustment_movement(list_ids, new_origin_id, reason, type, user_id):
    tracker_detail_products = TrackerDetailProductModel.objects.filter(
        available_quantity__gt=0
    ).exclude(id__in=list_ids)
    for tracker_detail_product in tracker_detail_products:
        if tracker_detail_product.available_quantity > 0:
            data = {
                "origin_id": new_origin_id,
                "tracker_detail_product_id": tracker_detail_product.id,
                "quantity": -tracker_detail_product.available_quantity,
                "module": InventoryMovementModel.Module.ADMIN,
                "movement_type": type,
                "reason": reason,
                "user_id": user_id
            }
            new_inv = InventoryMovementModel.objects.create(**data)
            new_inv.save()