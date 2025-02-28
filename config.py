import os
from dotenv import load_dotenv

load_dotenv(os.path.join(".env"))

SECRET_KEY = os.environ.get("SECRET_KEY")
DEBUG = os.environ.get("DEBUG", "False").lower() in ("true", "1", "t")
ALLOWED_HOSTS = [host.strip()
                 for host in os.environ.get("ALLOWED_HOSTS", "").split(",")]
CSRF_TRUSTED_ORIGINS = [url.strip() for url in os.environ.get(
    "CSRF_TRUSTED_ORIGINS", "").split(",")]
PORT = int(os.environ.get("PORT", 8000))

# Postgres db informations
DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT")
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")

# Telegram bot
BOT_API_TOKEN = os.environ.get("BOT_API_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
TG_GROUP_ID = os.environ.get("TG_GROUP_ID")

# OpenAI
OPENAI_API_TOKEN = os.environ.get("OPENAI_API_TOKEN")
ALPR_TOKEN = os.environ.get("ALPR_TOKEN")

# Redis
REDIS_HOST = os.environ.get("REDIS_HOST")
REDIS_PORT = int(os.environ.get("REDIS_PORT"))
REDIS_DB = int(os.environ.get("REDIS_DB"))