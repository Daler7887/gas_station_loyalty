from django.contrib import admin
from bot.models import *
from django.utils.html import format_html
from django.urls import reverse, path
from asgiref.sync import async_to_sync
from bot.utils.bot_functions import send_newsletter, bot


class Bot_userAdmin(admin.ModelAdmin):
    def get_list_display(self, request):
        if request.user.is_superuser:
            list_display = ['name', 'username',
                            'phone', 'car', 'date', 'edit_button']
        else:
            list_display = ['name', 'username', 'phone', 'car', 'date']
        return list_display
    search_fields = ['name', 'username', 'phone', 'car__plate_number']
    list_filter = ['date']
    list_display_links = None

    def edit_button(self, obj):
        change_url = reverse('admin:bot_bot_user_change', args=[obj.id])
        return format_html('<a class="btn btn-primary" href="{}"><i class="fas fa-edit"></i></a>', change_url)
    edit_button.short_description = 'Действие'


class Bot_userInline(admin.StackedInline):
    model = Bot_user
    extra = 0
    fields = ['name', 'username', 'phone', 'car', 'date']
    readonly_fields = ['name', 'username', 'phone', 'car', 'date']
    can_delete = False
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class MesageAdmin(admin.ModelAdmin):
    list_display = ['bot_users_name', 'small_text',
                    'open_photo', 'open_video', 'open_file', 'date']
    fieldsets = (
        ('', {
            'fields': ['bot_users', 'text', 'photo', 'video', 'file'],
            'description': 'Выберите пользователей, которым вы хотите отправить сообщение, или просто оставьте поле пустым, чтобы отправить всем пользователям.',
        }),

    )
    actions = ['send_message']
    filter_horizontal = ['bot_users',]

    def bot_users_name(self, obj):
        result = ''
        if users := obj.bot_users.all():
            for user in users:
                result += f'{user.name} {user.phone} | '
        else:
            result = 'Все'
        return result
    bot_users_name.short_description = 'Пользователи бота'

    def small_text(self, obj):
        cut_text = obj.text[:20] + ' ...' if len(obj.text) >= 20 else obj.text
        return format_html(f'<p title={obj.text}>{cut_text}</p>')
    small_text.short_description = 'Текст'

    def open_photo(self, obj):
        if obj.photo:
            change_url = f'/files/{obj.photo}'
            return format_html('<a target="_blank" class="btn btn-success" href="{}"><i class="fas fa-eye"></i> Открыть</a>', change_url)
        return None
    open_photo.short_description = 'Фото'

    def open_video(self, obj):
        if obj.video:
            change_url = f'/files/{obj.video}'
            return format_html('<a target="_blank" class="btn btn-warning" href="{}"><i class="fas fa-eye"></i> Открыть</a>', change_url)
        return None
    open_video.short_description = 'Видео'

    def open_file(self, obj):
        if obj.file:
            change_url = f'/files/{obj.file}'
            return format_html('<a target="_blank" class="btn btn-primary" href="{}"><i class="fas fa-eye"></i> Открыть</a>', change_url)
        return None
    open_file.short_description = 'Файл'

    def get_form(self, request, obj=None, **kwargs):
        form = super(MesageAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['bot_users'].widget.attrs['style'] = 'width: 20em;'
        return form

    def send_message(self, request, queryset):
        for message in queryset:

            users = message.bot_users.all()
            if not users:
                users = Bot_user.objects.all()
            for user in users:
                try:
                    photo = message.photo.path if message.photo else None
                    video = message.video.path if message.video else None
                    file = message.file.path if message.file else None
                    async_to_sync(send_newsletter)(bot, user.user_id, message.text,
                                                   photo=photo, video=video, document=file)
                except Exception as e:
                    self.message_user(
                        request, f"Ошибка при отправке сообщения пользователю {user}: {e}", level="error")

        self.message_user(request, "Сообщения успешно отправлены")
    send_message.short_description = "Разослать сообщения"


class SocialNetworkAdmin(admin.ModelAdmin):
    list_display = ('name', 'url')


class BranchAdmin(admin.ModelAdmin):
    list_display = ('name_ru', 'name_uz', 'message_ru', 'message_uz')


class FeedbackAdmin(admin.ModelAdmin):
    list_display = ['user_id', 'timestamp', 'text', 'photo', 'video', 'file']
    search_fields = ['user_id', 'text']
    list_filter = ['timestamp']


admin.site.register(Bot_user, Bot_userAdmin)
admin.site.register(Message, MesageAdmin)
admin.site.register(Feedback, FeedbackAdmin)
