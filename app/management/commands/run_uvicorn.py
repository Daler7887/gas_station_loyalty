from django.core.management.base import BaseCommand
from bot.control.updater import application
import asyncio
import os
import sys
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import signal
import uvicorn
from config import PORT

# This function will be called when a shutdown signal is received


def handle_shutdown(signal, frame):
    print("Received shutdown signal")
    # Stop the event loop
    loop = asyncio.get_event_loop()
    loop.stop()


# Register signal handlers for graceful shutdown
signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)


async def serve():
    config = uvicorn.Config("core.asgi:application",
                            host="127.0.0.1", port=PORT, log_level="info")
    server = uvicorn.Server(config)
    # await server.serve()
    async with application:
        await application.start()
        print("Bot is running...")
        await server.serve()
        await application.stop()


class RestartOnChangeHandler(FileSystemEventHandler):
    def __init__(self, restart_callback):
        self.restart_callback = restart_callback

    def on_modified(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith(('.py', '.html', '.css', '.js')):
            self.restart_callback()

    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith(('.py', '.html', '.css', '.js')):
            self.restart_callback()


class Command(BaseCommand):
    help = 'Start uvicron server'

    def handle(self, *args, **options):
        observer = Observer()
        event_handler = RestartOnChangeHandler(self.restart)
        observer.schedule(event_handler, path='.', recursive=True)
        observer.start()
        try:
            asyncio.run(
                serve()
            )
        except KeyboardInterrupt:
            observer.stop()
        observer.join()

    def restart(self):
        print("Restarting..\n\n")
        """Restart the current process."""
        os.execv(sys.executable, ['python'] + sys.argv)