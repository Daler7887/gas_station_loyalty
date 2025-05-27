from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import pandas as pd
from telegram import Bot
from asgiref.sync import async_to_sync
import os
from config import REPORT_BOT_TOKEN, REPORT_CHAT_ID
from django.db.models import Sum, Avg, Q
from app.models import FuelSale, Car, LoyaltyPointsTransaction
from app.utils import PLATE_NUMBER_TEMPLATE 
from decimal import Decimal

REPORT_BOT_TOKEN="6729597621:AAHrbjeHyIDfAdSPaLLNHWEmzNC6RsvvJnI"
REPORT_CHAT_ID="-706300022R"


def format_value(x):
    if isinstance(x, (int, float, Decimal)):
        return f"{x:,.2f}".replace(",", " ").replace(".00", "") if isinstance(x, int) or x == int(x) else f"{x:,.2f}".replace(",", " ")
    return x

def generate_sales_report(report_date: datetime, output_path="sales_report.jpg"):
    # Calculate date range for yesterday
    start_date = datetime.combine(report_date.date(), datetime.min.time())
    end_date = datetime.combine(report_date.date(), datetime.max.time())

    # total sales quantity
    total_quantity = FuelSale.objects.filter(date__range=(start_date, end_date)).aggregate(Sum('quantity'))['quantity__sum'] or 0

    # blacklist quantity
    blacklist_cars = FuelSale.objects.filter(
        date__range=(start_date, end_date),
        plate_number__in=Car.objects.filter(is_blacklisted=True).values_list('plate_number', flat=True)
    ).aggregate(Sum('quantity'))['quantity__sum'] or 0

    # invalid plates quantity
    null_plate_quantity = FuelSale.objects.filter(
        date__range=(start_date, end_date),
        plate_recognition__isnull=True
    ).aggregate(Sum('quantity'))['quantity__sum'] or 0
    invalid_plate_quantity = FuelSale.objects.filter(
        date__range=(start_date, end_date),
        plate_recognition__isnull=False
    ).exclude(
        plate_number__regex=PLATE_NUMBER_TEMPLATE
    ).aggregate(Sum('quantity'))['quantity__sum'] or 0
    total_invalid_plate_quantity = null_plate_quantity + invalid_plate_quantity

    price = FuelSale.objects.filter(date__range=(start_date, end_date)).aggregate(Avg('price'))['price__avg'] or 0
    if price == 0:
        print("Нет продаж за указанный период или цена равна нулю.")
        return
    
    discount = FuelSale.objects.filter(date__range=(start_date, end_date), discount_amount__gt=0).aggregate(Sum('quantity'), Sum('discount_amount'))
    discount_quantity = discount['quantity__sum'] or 0
    discount_amount = discount['discount_amount__sum'] or 0

    net_quantity = Decimal(total_quantity) - Decimal(discount_quantity) - Decimal(blacklist_cars) - Decimal(total_invalid_plate_quantity)
    total_sales_sum = net_quantity * price if price else 0

    bonus_accrual = LoyaltyPointsTransaction.objects.filter(
        (
            Q(fuel_sale__date__range=(start_date, end_date)) |
            (Q(fuel_sale=None) & Q(created_at__range=(start_date, end_date)))
        ),
        transaction_type='accrual'
    ).aggregate(Sum('points'))['points__sum'] or 0

    # Prepare data for the report

    data = {
        "Итого продажа": total_quantity,
        "Черный список куб": blacklist_cars,
        "Номер не опознан": total_invalid_plate_quantity,
        "Оплата бонус": discount_quantity,
        "Остаток куб": net_quantity,
        "Цена": price,
        "Сумма": total_sales_sum,
        "Начислено бонус": bonus_accrual,
        "Оплата по бонусам": discount_amount,
    }

    # Prepare table data
    columns = ["", ""]
    rows = [[key, format_value(value)] for key, value in data.items()]
    df = pd.DataFrame(rows, columns=columns)

    # Generate image
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.axis('off')
    table = ax.table(cellText=df.values, cellLoc='center', loc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2)

    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close()


async def send_telegram_report(image_path: str, bot_token: str, chat_id: str, caption: str = "📊 Отчет по продажам"):
    bot = Bot(token=bot_token)
    with open(image_path, 'rb') as img:
        await bot.send_photo(chat_id=chat_id, photo=img, caption=caption)


def send_sales_report():
    """
    Генерирует отчет о продажах и отправляет его в Telegram.
    """
    if not REPORT_BOT_TOKEN or not REPORT_CHAT_ID:
        print("Отсутствуют токен бота или ID чата для отправки отчета.")
        return

    report_date = datetime.now() - timedelta(days=1)  # Отчет за вчера
    output_path = "sales_report.jpg"  # Путь к файлу для сохранения отчета
    generate_sales_report(report_date, output_path)
    
    # Отправка отчета в Telegram
    async_to_sync(send_telegram_report)(
        image_path=output_path, 
        bot_token=REPORT_BOT_TOKEN, 
        chat_id=REPORT_CHAT_ID,
        caption=f"📊 Отчет по детальным продажам и бонусам за {report_date.strftime('%d.%m.%Y')}"
    )

    # Удаление файла после отправки
    if os.path.exists(output_path):
        os.remove(output_path)
