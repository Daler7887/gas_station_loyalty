from django.db import models
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
import re


class Bot_user(models.Model):
    user_id = models.BigIntegerField(null=True)

    name = models.CharField(null=True, blank=True,
                            max_length=256, default='', verbose_name='Имя')
    username = models.CharField(
        null=True, blank=True, max_length=256, verbose_name='username')
    firstname = models.CharField(
        null=True, blank=True, max_length=256, verbose_name='Никнейм')
    phone = models.CharField(null=True, blank=True,
                             max_length=16, default='', verbose_name='Телефон')
    lang = models.CharField(null=True, blank=True,
                            max_length=4, verbose_name='')
    date = models.DateTimeField(
        db_index=True, null=True, auto_now_add=True, blank=True, verbose_name='Дата регистрации')
    car = models.ForeignKey('app.Car', on_delete=models.CASCADE,
                            null=True, blank=True, verbose_name='Автомобиль')

    def __str__(self) -> str:
        try:
            return self.name + ' ' + str(self.phone)
        except:
            return super().__str__()

    class Meta:
        verbose_name = "Пользователь бота"
        verbose_name_plural = "Пользователи бота"


class Feedback(models.Model):
    user_id = models.ForeignKey(
        Bot_user, on_delete=models.CASCADE, verbose_name='Пользователь')
    message_id = models.CharField(max_length=50)
    admin_message_id = models.CharField(max_length=50, default='')
    admin_chat_id = models.CharField(max_length=50, default='')
    text = models.TextField(null=True, blank=True, verbose_name='Сообщение')
    photo = models.CharField(null=True, blank=True, max_length=255)
    video = models.CharField(null=True, blank=True, max_length=255)
    file = models.CharField(null=True, blank=True, max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='Дата')

    def __str__(self):
        return f'Отзыв от {self.user_id.phone} Сообщение: {self.text}'

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"


class Message(models.Model):
    bot_users = models.ManyToManyField(
        'bot.Bot_user', blank=True, related_name='bot_users_list', verbose_name='Пользователи бота')
    text = models.TextField(null=True, blank=False,
                            max_length=1024, verbose_name='Текст')
    photo = models.FileField(null=True, blank=True, upload_to="message/photo/", verbose_name='Фото',
                             validators=[FileExtensionValidator(
                                 allowed_extensions=['jpg', 'jpeg', 'png', 'bmp', 'gif'])]
                             )
    video = models.FileField(
        null=True, blank=True, upload_to="message/video/", verbose_name='Видео',
        validators=[FileExtensionValidator(
            allowed_extensions=['MOV', 'avi', 'mp4', 'webm', 'mkv'])]
    )
    file = models.FileField(null=True, blank=True,
                            upload_to="message/file/", verbose_name='Файл')
    is_sent = models.BooleanField(default=False)
    date = models.DateTimeField(
        db_index=True, null=True, auto_now_add=True, blank=True, verbose_name='Дата')

    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"
