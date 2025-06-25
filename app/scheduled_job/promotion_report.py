from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
from telegram import Bot
from asgiref.sync import async_to_sync
import os
from app.utils.queries import get_fuel_sales_breakdown_by_pump
from app.models import Car
from django.db.models import Q
from app.utils import PLATE_NUMBER_TEMPLATE


REPORT_BOT_TOKEN = "6729597621:AAHrbjeHyIDfAdSPaLLNHWEmzNC6RsvvJnI" 
REPORT_CHAT_ID = "-706300022"  # Замените на ваш ID чата


def format_value(x):
    if isinstance(x, (int, float)):
        return f"{x:,.0f}".replace(",", " ")
    return x


def generate_promotion_report(report_date: datetime, output_path="promotion_report.jpg"):
    # Calculate date range for yesterday
    start_date = datetime.combine(report_date.date(), datetime.min.time())
    end_date = datetime.combine(report_date.date(), datetime.max.time())
    # Fetch pump sales data
    pump_sales_data = get_fuel_sales_breakdown_by_pump(start_date, end_date, report_date)
    # Prepare table data
    columns = [
        "Колонка", 
        "Всего", 
        "Были зарег.",
        "Не были зарег.\n(старые)",
        "Не были зарег.\n(новые)",
        "Зарегистр.\n(старые)",
        "Зарегистр.\n(новые)"
    ]

    rows = []

    for pump_data in pump_sales_data:
        rows.append([
            pump_data.get("pump_name", "-"),
            format_value(pump_data.get("total", 0)),
            format_value(pump_data.get("was_registered", 0)),
            format_value(pump_data.get("unregistered_old", 0)),
            format_value(pump_data.get("unregistered_new", 0)),
            format_value(pump_data.get("registered_today_old", 0)),
            format_value(pump_data.get("registered_today_new", 0))
        ])

    # Add totals row if data exists
    if rows:
        total_row = [
            "Итого",
            format_value(sum(pump.get("total", 0) for pump in pump_sales_data)),
            format_value(sum(pump.get("was_registered", 0) for pump in pump_sales_data)),
            format_value(sum(pump.get("unregistered_old", 0) for pump in pump_sales_data)),
            format_value(sum(pump.get("unregistered_new", 0) for pump in pump_sales_data)),
            format_value(sum(pump.get("registered_today_old", 0) for pump in pump_sales_data)),
            format_value(sum(pump.get("registered_today_new", 0) for pump in pump_sales_data))
        ]
        rows.append(total_row)

    registered_total = Car.objects.filter(
        Q(bot_user__isnull=False, bot_user__date__lt=report_date.date()) |
        Q(is_blacklisted=True)
    ).values('plate_number').distinct().count()
    total_cars = Car.objects.filter(plate_number__regex=PLATE_NUMBER_TEMPLATE).count()
    data2 = [
        ["Всего автомобилей", format_value(total_cars)],
        ["Зарегистрированных", format_value(registered_total)],
        ["Процент зарегистрированных", format_value(f"{(registered_total / total_cars * 100 if total_cars != 0 else 0):.2f}%")]
    ]

    df = pd.DataFrame(rows, columns=columns)
    if df.empty:
        print("Нет данных для формирования отчета.")
        return

    # Generate image
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.axis('off')
    table1 = ax.table(
            cellText=df.values,
            cellLoc='center',
            colLabels=df.columns,
            loc='center'
        )

    table1.auto_set_font_size(False)
    table1.set_fontsize(10)
    table1.scale(1.2, 1.8)
    

    table2 = ax.table(cellText=data2, cellLoc="center", loc="upper center", bbox=[0, -0.2, 1, 0.3])
    table2.auto_set_font_size(False)
    table2.set_fontsize(10)
    table2.scale(1, 1.5)

    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close()
    

async def send_telegram_report(image_path: str, bot_token: str, chat_id: str, caption: str = "📊 Отчет по продвижению"):
    bot = Bot(token=bot_token)
    with open(image_path, 'rb') as img:
        await bot.send_photo(chat_id=chat_id, photo=img, caption=caption)


def send_promotion_report():
    """
    Генерирует отчет о продвижении и отправляет его в Telegram.
    """
    if not REPORT_BOT_TOKEN or not REPORT_CHAT_ID:
        print("Отсутствуют токен бота или ID чата для отправки отчета.")
        return

    report_date = datetime.now() - timedelta(days=1)  # Отчет за вчера
    output_path = "promotion_report.jpg"  # Путь к файлу для сохранения отчета
    generate_promotion_report(report_date, output_path)

    # Отправка отчета в Telegram
    async_to_sync(send_telegram_report)(
        image_path=output_path,
        bot_token=REPORT_BOT_TOKEN,
        chat_id=REPORT_CHAT_ID,
        caption=f"📊 Отчет по продвижению за {report_date.strftime('%d.%m.%Y')}"
    )

    # Удаление файла после отправки
    if os.path.exists(output_path):
        os.remove(output_path)