import json
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from bot.control.updater import application
from telegram import Update
import logging

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class BotWebhookView(View):
    async def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body.decode("utf-8"))
            update = Update.de_json(data=data, bot=application.bot)
            await update_bot(update)
            return JsonResponse({'status': 'success'})
        except Exception as e:
            logger.error(f"Error handling webhook: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)})

async def update_bot(update):
    logger.info(f"Putting update into queue: {update}")
    await application.update_queue.put(update)