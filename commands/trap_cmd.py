import logging
import random
from pyrogram import Client, filters
from pyrogram.types import Message
from collections import defaultdict
from utils.filters import simple_cmd_filter

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Словарь для хранения активных ловушек по chat_id
active_traps = defaultdict(dict)

async def trap_command(client: Client, message: Message):
    try:
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        # Удаляем сообщение с командой
        await message.delete()
        
        # Отправляем первую картинку
        trap_msg = await client.send_photo(
            chat_id=chat_id,
            photo="resources/lovushka1.jpg",
            caption="Ловушка установлена! Ждём жертву..."
        )
        
        # Сохраняем информацию о ловушке
        active_traps[chat_id] = {
            'user_id': user_id,
            'message_id': trap_msg.id,
            'active': True
        }
        
        logger.info(f"Ловушка установлена в чате {chat_id} пользователем {user_id}")

    except Exception as e:
        logger.error(f"Ошибка в trap_command: {e}")

async def handle_trap_reply(client: Client, message: Message):
    try:
        chat_id = message.chat.id
        
        # Проверяем есть ли активная ловушка в этом чате
        if chat_id not in active_traps or not active_traps[chat_id]['active']:
            return
            
        trap = active_traps[chat_id]
        
        # Если сообщение от того же пользователя, что и установил ловушку
        if message.from_user.id == trap['user_id']:
            # Отправляем первую картинку
            await client.send_photo(
                chat_id=chat_id,
                photo="resources/lovushka1.jpg",
                reply_to_message_id=message.id
            )
            return
        
        # Если сообщение от другого пользователя
        if message.from_user.id != trap['user_id']:
            # Отправляем вторую картинку с реплаем
            await client.send_photo(
                chat_id=chat_id,
                photo="resources/lovushka2.jpg",
                reply_to_message_id=message.id
            )
            
            # Деактивируем ловушку
            active_traps[chat_id]['active'] = False
            logger.info(f"Ловушка сработала в чате {chat_id} на пользователе {message.from_user.id}")

    except Exception as e:
        logger.error(f"Ошибка в handle_trap_reply: {e}")

def register(app: Client):
    app.on_message(simple_cmd_filter("ловушка", ignore_case=True) & filters.me)(trap_command)
    app.on_message(filters.group & ~filters.service)(handle_trap_reply)