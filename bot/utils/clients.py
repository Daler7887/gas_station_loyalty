from django.db.models import Sum
from bot.models import Bot_user
from app.models import FuelSale, Constant
from bot.utils.bot_functions import bot_send_message
from asgiref.sync import async_to_sync

def get_user_bonus(user: Bot_user):
    bonus = 0
    # Суммируем total_amount для каждого пользователя по plate_number
    total_amount = FuelSale.objects.filter(plate_recognition__number=user.plate_number).aggregate(
        Sum('total_amount'))['total_amount__sum']

    # Если total_amount None (нет продаж), устанавливаем 0
    if total_amount:
        bonus = total_amount * get_bonus_percent() / 100 or 0
    return bonus


def get_bonus_percent():
    # Находим объект с ключом `bonus_percent`
    constant = Constant.objects.filter(key='bonus_percent').first()
    if constant:
        # Предполагается, что значение хранится в поле `value`
        return int(constant.value)
    return 0


def inform_user_bonus(user: Bot_user):
    bonus = get_user_bonus(user)
    msg = "Начался процесс заправки вашего автомобиля. На вашем балансе бонус в размере {} сум".format(bonus)
    bot_send_message(user.user_id, msg)

    
