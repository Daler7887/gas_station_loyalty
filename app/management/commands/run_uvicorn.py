from django.core.management.base import BaseCommand
from bot.control.updater import application
import asyncio
import os
import sys
import signal
import uvicorn
from config import PORT
import logging

logger = logging.getLogger(__name__)

# This function will be called when a shutdown signal is received
def handle_shutdown(signal, frame):
    loop = asyncio.get_event_loop()
    loop.stop()

# Register signal handlers for graceful shutdown
signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)

async def serve():
    config = uvicorn.Config("core.asgi:application", host="127.0.0.1", port=PORT, log_level="info")
    server = uvicorn.Server(config)
    async with application:
        await application.start()
        await server.serve()
        await application.stop()

class Command(BaseCommand):
    help = 'Start uvicorn server'

    def handle(self, *args, **options):
        try:
            asyncio.run(serve())
        except KeyboardInterrupt:
            logger.info("Server stopped manually")