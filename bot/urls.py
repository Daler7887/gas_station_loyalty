from django.urls import path, re_path
from bot.views.botwebhook import BotWebhookView
from config import BOT_API_TOKEN

urlpatterns = [
    path(BOT_API_TOKEN, BotWebhookView.as_view())
]
