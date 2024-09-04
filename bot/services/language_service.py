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