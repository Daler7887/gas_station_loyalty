from django.db.models.signals import post_save, post_delete
from django.db.models import Sum
from django.dispatch import receiver
from .models import LoyaltyPointsTransaction, PlateRecognition, FuelSale
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .utils.queries import get_pump_info


@receiver(post_save, sender=LoyaltyPointsTransaction)
def loyalty_points_transaction_saved(sender, instance, created, **kwargs):
    """
    Обрабатывает создание или обновление записи Bot_user при создании LoyaltyPointsTransaction.
    """
    update_car_loyalty_points(instance.car)
    # channel_layer = get_channel_layer()
    # pump_info = get_pump_info()
    # async_to_sync(channel_layer.group_send)(
    #     'pumps_group',
    #     {
    #         'type': 'pump_message',
    #         'pumps': pump_info
    #     }
    # )


@receiver(post_delete, sender=LoyaltyPointsTransaction)
def loyalty_points_transaction_deleted(sender, instance, **kwargs):
    """
    Обрабатывает удаление записи LoyaltyPointsTransaction.
    """
    update_car_loyalty_points(instance.car)


@receiver(post_save, sender=FuelSale)
def update_fuel_sale_info(sender, instance, created, **kwargs):
    if not created:
        org_id = instance.organization_id
        channel_layer = get_channel_layer()
        pump_info = get_pump_info(org_id)
        async_to_sync(channel_layer.group_send)(
            f'pumps_org_{org_id}',
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

    org_id = instance.organization.id
    channel_layer = get_channel_layer()
    pump_info = get_pump_info(org_id)
    async_to_sync(channel_layer.group_send)(
        f'pumps_org_{org_id}',
        {
            'type': 'pump_message',
            'pumps': pump_info
        }
    )


def update_car_loyalty_points(car):
    accrual_points = LoyaltyPointsTransaction.objects.filter(
        car=car, transaction_type='accrual').aggregate(Sum('points'))['points__sum'] or 0
    redeem_points = LoyaltyPointsTransaction.objects.filter(
        car=car, transaction_type='redeem').aggregate(Sum('points'))['points__sum'] or 0
    total_points = accrual_points - redeem_points
    car.loyalty_points = total_points
    car.save(update_fields=['loyalty_points'])
