from django.db.models import Sum
from ..models.product_inventory import ProductInventoryModel
from ..models.detail import OrderDetailModel
from ..models.order import OrderModel

def get_product_available_quantity(product, distributor_center, expiration_date=None):
    """
    Obtiene la cantidad disponible de un producto en un centro de distribución
    """
    try:
        inventory = ProductInventoryModel.objects.get(
            product=product,
            distributor_center=distributor_center,
            expiration_date=expiration_date
        )
        return inventory.available_quantity
    except ProductInventoryModel.DoesNotExist:
        return 0

def get_product_reserved_quantity(product, distributor_center, expiration_date=None, exclude_order_detail=None):
    """
    Calcula la cantidad total reservada de un producto en órdenes pendientes/en proceso
    """
    queryset = OrderDetailModel.objects.filter(
        product=product,
        distributor_center=distributor_center,
        expiration_date=expiration_date,
        order__status__in=[OrderModel.OrderStatus.PENDING, OrderModel.OrderStatus.IN_PROCESS]
    )
    
    if exclude_order_detail:
        queryset = queryset.exclude(id=exclude_order_detail.id)
    
    result = queryset.aggregate(total=Sum('quantity'))
    return result['total'] or 0

def validate_product_quantity(product, distributor_center, quantity, expiration_date=None, exclude_order_detail=None):
    """
    Valida si hay suficiente cantidad disponible de un producto
    """
    available = get_product_available_quantity(product, distributor_center, expiration_date)
    reserved = get_product_reserved_quantity(product, distributor_center, expiration_date, exclude_order_detail)
    
    # La cantidad disponible menos lo ya reservado debe ser mayor o igual a la cantidad solicitada
    return (available - reserved) >= quantity

def reserve_product_quantity(product, distributor_center, quantity, expiration_date=None):
    """
    Reserva cantidad de producto para una orden
    """
    try:
        inventory = ProductInventoryModel.objects.get(
            product=product,
            distributor_center=distributor_center,
            expiration_date=expiration_date
        )
        inventory.reserve_quantity(quantity)
        return True
    except ProductInventoryModel.DoesNotExist:
        return False
    except ValueError:
        return False

def release_product_quantity(product, distributor_center, quantity, expiration_date=None):
    """
    Libera cantidad reservada de producto (cancelación de orden)
    """
    try:
        inventory = ProductInventoryModel.objects.get(
            product=product,
            distributor_center=distributor_center,
            expiration_date=expiration_date
        )
        inventory.release_quantity(quantity)
        return True
    except ProductInventoryModel.DoesNotExist:
        return False
    except ValueError:
        return False

def consume_product_quantity(product, distributor_center, quantity, expiration_date=None):
    """
    Consume cantidad reservada de producto (orden completada)
    """
    try:
        inventory = ProductInventoryModel.objects.get(
            product=product,
            distributor_center=distributor_center,
            expiration_date=expiration_date
        )
        inventory.consume_quantity(quantity)
        return True
    except ProductInventoryModel.DoesNotExist:
        return False
    except ValueError:
        return False

def create_or_update_product_inventory(product, distributor_center, quantity, expiration_date=None):
    """
    Crea o actualiza el inventario de un producto
    """
    inventory, created = ProductInventoryModel.objects.get_or_create(
        product=product,
        distributor_center=distributor_center,
        expiration_date=expiration_date,
        defaults={
            'total_quantity': quantity,
            'available_quantity': quantity,
            'reserved_quantity': 0
        }
    )
    
    if not created:
        inventory.add_inventory(quantity)
    
    return inventory