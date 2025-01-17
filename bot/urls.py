from django.urls import path, re_path
from bot.views import botwebhook
from config import BOT_API_TOKEN

urlpatterns = [
    path(BOT_API_TOKEN, botwebhook.bot_webhook)
]