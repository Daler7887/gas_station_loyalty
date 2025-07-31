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


def generate_balance_report(report_date: datetime, output_path="bonus_report.jpg"):
    start_day = datetime.combine(report_date.date(), time.min)
    mid_day = datetime.combine(report_date.date(), time(12, 0))
    end_day = datetime.combine(report_date.date(), time.max)

    # Баланс на начало
    initial = LoyaltyPointsTransaction.objects.filter(created_at__lt=start_day).aggregate(
        accrued=Sum('points', filter=Q(transaction_type='accrual')),
        redeemed=Sum('points', filter=Q(transaction_type='redeem')),
    )
    start_balance = (initial['accrued'] or 0) - (initial['redeemed'] or 0)

    # Получаем все организации
    orgs = LoyaltyPointsTransaction.objects.values_list('organization_id', flat=True).distinct()

    def get_period_data(start, end):
        """Возвращает словарь вида {org_id: {'accrual': X, 'redeem': Y}}"""
        qs = LoyaltyPointsTransaction.objects.filter(created_at__gte=start, created_at__lt=end)
        data = {}
        for org_id in orgs:
            accrued = qs.filter(transaction_type='accrual', organization_id=org_id).aggregate(total=Sum('points'))['total'] or 0
            redeemed = qs.filter(transaction_type='redeem', organization_id=org_id).aggregate(total=Sum('points'))['total'] or 0
            data[org_id] = {'accrual': accrued, 'redeem': redeemed}
        return data

    morning_data = get_period_data(start_day, mid_day)
    evening_data = get_period_data(mid_day, end_day)

    # Итого по движениям
    total_data = {}
    for org_id in orgs:
        total_data[org_id] = {
            'accrual': morning_data.get(org_id, {}).get('accrual', 0) + evening_data.get(org_id, {}).get('accrual', 0),
            'redeem': morning_data.get(org_id, {}).get('redeem', 0) + evening_data.get(org_id, {}).get('redeem', 0)
        }

    # Итоговый баланс
    total_accrued = sum(v['accrual'] for v in total_data.values())
    total_redeemed = sum(v['redeem'] for v in total_data.values())
    end_balance = start_balance + total_accrued - total_redeemed

    # Формируем таблицу
    columns = ["Период", "Остаток на начало"]
    for org_id in orgs:
        columns.append(f"Начислено ({org_id})")
        columns.append(f"Списано ({org_id})")
    columns.append("Остаток на конец")

    def build_row(label, period_data, starting_balance, ending_balance):
        row = [label, starting_balance]
        for org_id in orgs:
            row.append(period_data.get(org_id, {}).get('accrual', 0))
            row.append(period_data.get(org_id, {}).get('redeem', 0))
        row.append(ending_balance)
        return row

    mid_balance = start_balance + sum(v['accrual'] - v['redeem'] for v in morning_data.values())
    rows = [
        build_row("00.00 - 11.59", morning_data, start_balance, mid_balance),
        build_row("12.00 - 23.59", evening_data, mid_balance, end_balance),
    ]

    # Строка Итого
    rows.append(build_row("Итого", total_data, start_balance, end_balance))

    df = pd.DataFrame(rows, columns=columns)
    formatted_df = df.applymap(format_number)  # Применить форматирование, если нужно

    # Визуализация
    fig, ax = plt.subplots(figsize=(len(columns) * 1.1, 3))
    ax.axis('off')
    table = ax.table(cellText=formatted_df.values, colLabels=columns, cellLoc='center', loc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 2)

    # Выделение итогов
    last_row_idx = len(df) - 1
    for col_idx in range(len(columns)):
        cell = table[last_row_idx + 1, col_idx]  # +1 из-за заголовка
        cell.set_fontsize(10)
        cell.set_text_props(weight='bold')
        cell.set_facecolor('#f0f0f0')

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
    # Установка контекста для организации
    output_path = f"bonus_report.jpg"  # Путь к файлу для сохранения отчета
    generate_balance_report(report_date, output_path)

    orgs = Organization.objects.all()
    for org in orgs:
        if org.report_chat_id is None:
            print(f"Отсутствует chat_id для организации {org.name}.")
            continue
        # Отправка отчета в Telegram
        async_to_sync(send_telegram_report)(
            image_path=output_path, 
            bot_token=REPORT_BOT_TOKEN, 
            chat_id=org.report_chat_id,
            caption=f"📊 Отчет по баллам за {report_date.strftime('%d.%m.%Y')}"
        )

    # Удаление файла после отправки
    if os.path.exists(output_path):
        os.remove(output_path)
