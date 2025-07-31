from datetime import datetime, time, timedelta
import matplotlib.pyplot as plt
import pandas as pd
from django.db.models import Sum, Q, Value as V
from django.db.models.functions import Coalesce
from app.models import LoyaltyPointsTransaction, Organization
from telegram import Bot
from asgiref.sync import async_to_sync
import os
from config import REPORT_BOT_TOKEN, REPORT_CHAT_ID


def format_number(x):
    return f"{x:,}".replace(",", " ") if isinstance(x, (int, float)) else x


def generate_balance_report(report_date: datetime, output_path: str = "bonus_report.jpg"):
    """Свод начислений/списаний бонусов по организациям за выбранную дату."""

    # ——— Границы суток ————————————————————————————————
    start_day = datetime.combine(report_date.date(), time.min)
    mid_day   = datetime.combine(report_date.date(), time(12, 0))
    end_day   = datetime.combine(report_date.date(), time.max)

    # ——— Остаток на начало дня ————————————————————————————
    initial = LoyaltyPointsTransaction.objects.filter(created_at__lt=start_day).aggregate(
        accrued = Sum('points', filter=Q(transaction_type='accrual')),
        redeemed = Sum('points', filter=Q(transaction_type='redeem')),
    )
    opening_balance = (initial['accrued'] or 0) - (initial['redeemed'] or 0)

    # ——— Агрегации по организациям за оба полу-дня (один запрос) ——
    org_qs = (
        Organization.objects
        .annotate(
            # Утро
            morn_accr = Coalesce(
                Sum(
                    'loyaltypointstransaction__points',
                    filter=Q(
                        loyaltypointstransaction__created_at__gte=start_day,
                        loyaltypointstransaction__created_at__lt=mid_day,
                        loyaltypointstransaction__transaction_type='accrual'
                    )
                ), V(0)
            ),
            morn_redm = Coalesce(
                Sum(
                    'loyaltypointstransaction__points',
                    filter=Q(
                        loyaltypointstransaction__created_at__gte=start_day,
                        loyaltypointstransaction__created_at__lt=mid_day,
                        loyaltypointstransaction__transaction_type='redeem'
                    )
                ), V(0)
            ),
            # Вечер
            eve_accr = Coalesce(
                Sum(
                    'loyaltypointstransaction__points',
                    filter=Q(
                        loyaltypointstransaction__created_at__gte=mid_day,
                        loyaltypointstransaction__created_at__lte=end_day,
                        loyaltypointstransaction__transaction_type='accrual'
                    )
                ), V(0)
            ),
            eve_redm = Coalesce(
                Sum(
                    'loyaltypointstransaction__points',
                    filter=Q(
                        loyaltypointstransaction__created_at__gte=mid_day,
                        loyaltypointstransaction__created_at__lte=end_day,
                        loyaltypointstransaction__transaction_type='redeem'
                    )
                ), V(0)
            ),
        )
        .order_by('name')     # чтобы столбцы были в стабильном порядке
    )

    # ——— Суммы по периодам (сразу считаем итоги) ——————————
    total_morn_accr = sum(org.morn_accr for org in org_qs)
    total_morn_redm = sum(org.morn_redm for org in org_qs)
    total_eve_accr  = sum(org.eve_accr  for org in org_qs)
    total_eve_redm  = sum(org.eve_redm  for org in org_qs)

    mid_balance  = opening_balance + total_morn_accr - total_morn_redm
    closing_balance = mid_balance + total_eve_accr - total_eve_redm

    # ——— Формируем строки ————————————————————————————————
    columns = (
        ["Период", "Начальный\nбаланс"] +
        [f"Начислено\n({org.name})" for org in org_qs] +
        [f"Списано\n({org.name})"   for org in org_qs] +
        ["Конечный\nбаланс"]
    )

    # ── собираем значения по-отдельности, а не одной «простынёй»
    morn_accr   = [org.morn_accr for org in org_qs]
    eve_accr    = [org.eve_accr  for org in org_qs]
    morn_redm   = [org.morn_redm for org in org_qs]
    eve_redm    = [org.eve_redm  for org in org_qs]

    total_accr_per_org = [m + e for m, e in zip(morn_accr, eve_accr)]
    total_redm_per_org = [m + e for m, e in zip(morn_redm, eve_redm)]

    row_morning = (["00:00–11:59", opening_balance] + morn_accr + morn_redm + [mid_balance])
    row_evening = (["12:00–23:59", mid_balance]      + eve_accr  + eve_redm  + [closing_balance])
    row_total   = (["Итого",       opening_balance]  + total_accr_per_org + total_redm_per_org + [closing_balance])

    data = [row_morning, row_evening, row_total]
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
