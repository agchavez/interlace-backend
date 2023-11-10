from ..models import TrackerModel
from apps.inventory.models import InventoryMovementModel
from django.db import transaction
from celery import shared_task
"""
Funcion para aplicar los movimientos de salida de un tracker cuando se da completado, ingresando cantidades a los movimientos de inventario 
son de salida y de tipo T1 
"""
@shared_task
@transaction.atomic
def apply_output_movements(tracker_id, user_id):
    # lista movimientos de salida
    list_process = []
    tracker = TrackerModel.objects.get(id=tracker_id)
    if tracker:
        cd = tracker.distributor_center
        list_out = tracker.tracker_detail_output.all()
        for out in list_out:
            tracker_detail_product = out.tracker_detail_product
            quantity_boxes = out.quantity * tracker_detail_product.tracker_detail.product.boxes_pre_pallet
            inventory_movement = InventoryMovementModel.objects.create(
                tracker_detail_product=tracker_detail_product,
                module=InventoryMovementModel.Module.T1,
                origin_id=tracker.id,
                movement_type=InventoryMovementModel.MovementType.OUT,
                quantity=-quantity_boxes,
                user_id=user_id
            )
            list_process.append(out.id)
            inventory_movement.save()
    return list_process



