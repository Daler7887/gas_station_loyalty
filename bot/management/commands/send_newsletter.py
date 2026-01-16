from django.core.management.base import BaseCommand
from bot.utils.bot_functions import send_newsletter, bot


class Command(BaseCommand):
    help = 'Command that send newsletter to bot users'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--message_id',
            type=int,
            help='ID of the message to be sent in the newsletter.',
        )
        parser.add_argument(
            '--start_id',
            type=int,
            help='ID of the user to start sending from.',
        )

    def handle(self, *args, **kwargs):
        from bot.models import Message, Bot_user
        from asgiref.sync import async_to_sync

        message_id = kwargs.get('message_id')
        start_id = kwargs.get('start_id')

        if not message_id:
            self.stdout.write('Please provide a valid --message_id argument.')
            return

        try:
            message = Message.objects.get(id=message_id)
        except Message.DoesNotExist:
            self.stdout.write(f'Message with ID {message_id} does not exist.')
            return

        users = message.bot_users.all()
        if not users:
            users = Bot_user.objects.all()

        total = users.count()
        for index, user in enumerate(users, start=start_id or 1):   
            try:
                photo = message.photo.path if message.photo else None
                video = message.video.path if message.video else None
                file = message.file.path if message.file else None
                text = message.text if user.lang != 'uz' else message.text_uz
                result = async_to_sync(send_newsletter)(bot, user.user_id, text, photo, video, file)
                if type(result) is Exception:
                    self.stderr.write(f'Failed to send message to {user.name}: {result}')
                else:
                    self.stdout.write(f'Sent message to {user.name} ({index}/{total})')

            except Exception as e:
                self.stderr.write(f'Failed to send message to {user.name}: {e}')

        self.stdout.write(self.style.SUCCESS('Newsletter sending completed.'))