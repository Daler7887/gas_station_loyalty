from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import LoyaltyPointsTransaction

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
