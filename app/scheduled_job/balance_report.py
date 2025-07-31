from datetime import datetime, time, timedelta
import matplotlib.pyplot as plt
import pandas as pd
from django.db.models import Sum, Q
from app.models import LoyaltyPointsTransaction, Organization
from telegram import Bot
from asgiref.sync import async_to_sync
import os
from config import REPORT_BOT_TOKEN, REPORT_CHAT_ID


def format_number(x):
    return f"{x:,}".replace(",", " ") if isinstance(x, (int, float)) else x


def generate_balance_report(report_date: datetime, org_id, output_path="bonus_report.jpg"):
    # Установка периодов
    if org_id is None:
        raise ValueError("Organization ID must be provided")
        
    start_day = datetime.combine(report_date.date(), time.min)
    mid_day = datetime.combine(report_date.date(), time(12, 0))
    end_day = datetime.combine(report_date.date(), time.max)

    # Баланс на начало
    initial = LoyaltyPointsTransaction.objects.filter(organization_id=org_id, created_at__lt=start_day).aggregate(
        accrued=Sum('points', filter=Q(transaction_type='accrual')),
        redeemed=Sum('points', filter=Q(transaction_type='redeem')),
    )
    start_balance = (initial['accrued'] or 0) - (initial['redeemed'] or 0)

    # Утро: 00.00 - 11.59
    morning = LoyaltyPointsTransaction.objects.filter(organization_id=org_id, created_at__gte=start_day, created_at__lt=mid_day)
    morning_accrued = morning.filter(transaction_type='accrual').aggregate(Sum('points'))['points__sum'] or 0
    morning_redeemed = morning.filter(transaction_type='redeem').aggregate(Sum('points'))['points__sum'] or 0

    # Вечер: 12.00 - 23.59
    evening = LoyaltyPointsTransaction.objects.filter(organization_id=org_id, created_at__gte=mid_day, created_at__lte=end_day)
    evening_accrued = evening.filter(transaction_type='accrual').aggregate(Sum('points'))['points__sum'] or 0
    evening_redeemed = evening.filter(transaction_type='redeem').aggregate(Sum('points'))['points__sum'] or 0

    # Расчеты
    mid_balance = start_balance + morning_accrued - morning_redeemed
    end_balance = mid_balance + evening_accrued - evening_redeemed
    total_accrued = morning_accrued + evening_accrued
    total_redeemed = morning_redeemed + evening_redeemed

    # Подготовка таблицы
    data = [
        ["00.00 - 11.59", start_balance, morning_accrued, morning_redeemed, mid_balance],
        ["12.00 - 23.59", mid_balance, evening_accrued, evening_redeemed, end_balance],
        ["Итого", start_balance, total_accrued, total_redeemed, end_balance],
    ]
    columns = ["Период", "Остаток на начало", "Начислено", "Списано", "Остаток на конец"]
    df = pd.DataFrame(data, columns=columns)

    formatted_df = df.applymap(format_number)

    # Генерация изображения
    fig, ax = plt.subplots(figsize=(10, 3))
    ax.axis('off')
    table = ax.table(cellText=formatted_df.values, colLabels=columns, cellLoc='center', loc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2)

    # Выделяю последнюю строку
    last_row_idx = len(df) - 1
    for col_idx in range(len(columns)):
        cell = table[last_row_idx + 1, col_idx]  # +1 — из-за заголовка
        cell.set_fontsize(10)
        cell.set_text_props(weight='bold')       # жирный шрифт
        cell.set_facecolor('#f0f0f0')            # светло-серый фон

    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close()


async def send_telegram_report(image_path: str, bot_token: str, chat_id: str, caption: str = "📊 Отчет по бонусам"):
    bot = Bot(token=bot_token)
    with open(image_path, 'rb') as img:
        await bot.send_photo(chat_id=chat_id, photo=img, caption=caption)


def send_balance_report():
    """
    Генерирует отчет о балансе бонусов и отправляет его в Telegram.
    """
    if not REPORT_BOT_TOKEN:
        print("Отсутствуют токен бота")
        return

    report_date = datetime.now() - timedelta(days=1)  # Отчет за вчера
    orgs = Organization.objects.all()
    for org in orgs:
        if org.report_chat_id is None:
            print(f"Отсутствует chat_id для организации {org.name}.")
            continue
        # Установка контекста для организации
        output_path = f"bonus_report_{org.id}.jpg"  # Путь к файлу для сохранения отчета
        generate_balance_report(report_date, org.id, output_path)
        
        # Отправка отчета в Telegram
        async_to_sync(send_telegram_report)(
            image_path=output_path, 
            bot_token=REPORT_BOT_TOKEN, 
            chat_id=org.report_chat_id,
            caption=f"📊 Отчет по баллам {org.name} за {report_date.strftime('%d.%m.%Y')}"
        )

        # Удаление файла после отправки
        if os.path.exists(output_path):
            os.remove(output_path)
