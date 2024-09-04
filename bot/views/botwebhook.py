import json
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from bot.control.updater import application
from telegram import Update
import asyncio
from asgiref.sync import sync_to_async
from time import sleep

@csrf_exempt
def bot_webhook(request):
    data = json.loads(request.body.decode("utf-8"))
    update = Update.de_json(data = data, bot=application.bot)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(update_bot(update))
    loop.close()
    return HttpResponse('')

async def update_bot(update):
    # await asyncio.sleep(5)
    async with application:
        await application.process_update(update)