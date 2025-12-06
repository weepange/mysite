# signals.py
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from .models import Order

@receiver(post_save, sender=Order)
def handle_order_save(sender, instance, created, **kwargs):
    """При сохранении заказа"""
    if created and instance.status != 'CANCELED':
        # Новый заказ - уменьшаем количество
        if instance.product.quantity >= instance.quantity:
            instance.product.quantity -= instance.quantity
            instance.product.save()
        # Если товара нет - ничего не делаем, просто заказ создан

@receiver(post_save, sender=Order)
def handle_order_status_change(sender, instance, **kwargs):
    """При изменении статуса заказа"""
    # Ничего не делаем - статусы меняем только через actions
    pass