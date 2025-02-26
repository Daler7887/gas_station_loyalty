from bot.models import *
from bot.resources.strings import lang_dict


async def get_word(text, update=None, chat_id=None):
    if not chat_id:
        chat_id = update.message.chat.id

    user = await Bot_user.objects.aget(user_id=chat_id)
    if user.lang == "uz":
        result = lang_dict[text][0]
    else:
        result = lang_dict[text][1]

    return result if result else text


def get_word_sync(texts, chat_id=None):
    user = Bot_user.objects.filter(user_id=chat_id).first()
    if user and user.lang == "uz":
        result = lang_dict[texts][0]
    else:
        result = lang_dict[texts][1]

    return result if result else texts