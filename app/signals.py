from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import LoyaltyPointsTransaction, PlateRecognition
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .utils.queries import get_pump_info


@receiver(post_save, sender=LoyaltyPointsTransaction)
def create_or_update_bot_user(sender, instance, created, **kwargs):
    """
    Обрабатывает создание или обновление записи Bot_user при создании LoyaltyPointsTransaction.
    """
    if created:
        # Обновляем баланс пользователя
        car = instance.car
        if instance.transaction_type == 'accrual':
            car.loyalty_points += instance.points
        elif instance.transaction_type == 'redeem':
            car.loyalty_points -= instance.points

        car.save()

    channel_layer = get_channel_layer()
    pump_info = get_pump_info()
    async_to_sync(channel_layer.group_send)(
        'pumps_group',
        {
            'type': 'pump_message',
            'pumps': pump_info
        }
    )


@receiver(post_save, sender=PlateRecognition)
def update_pump_info(sender, instance, created, **kwargs):
    """
    Обрабатывает создание или обновление записи PlateRecognition.
    """
    # Отправляем информацию о новой записи в группу WebSocket

    channel_layer = get_channel_layer()
    pump_info = get_pump_info()
    async_to_sync(channel_layer.group_send)(
        'pumps_group',
        {
            'type': 'pump_message',
            'pumps': pump_info
        }
    )
