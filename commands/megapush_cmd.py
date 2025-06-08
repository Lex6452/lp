from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ChatType
from pyrogram.errors import FloodWait
import asyncio
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Фильтр для команды .мегапуш
def megapush_filter(_: Client, __: any, message: Message):
    try:
        return (
            message.text is not None and
            message.text.startswith('.мегапуш') and
            message.chat is not None and
            message.chat.type in (ChatType.SUPERGROUP, ChatType.GROUP) and
            message.from_user and
            message.from_user.is_self
        )
    except Exception as e:
        logger.error(f"Ошибка в megapush_filter: {str(e)}, сообщение: {message.text}")
        return False

async def megapush_cmd(client: Client, message: Message):
    """Редактирует сообщение, добавляя push-теги всех участников чата."""
    try:
        if not message.chat.type in (ChatType.SUPERGROUP, ChatType.GROUP):
            await message.edit("❌ Эта команда работает только в групповых чатах или супергруппах!")
            return

        # Получаем участников чата
        usernames = []
        async for member in client.get_chat_members(message.chat.id):
            try:
                user = member.user
                if user.is_bot or user.is_deleted:
                    continue  # Пропускаем ботов и удалённые аккаунты
                if user.username:  # Проверяем, есть ли имя пользователя
                    usernames.append(f"@{user.username}")
            except Exception as e:
                logger.error(f"Ошибка при получении участника чата: {str(e)}")
                continue

        if not usernames:
            await message.edit("❌ В чате нет пользователей с @username или доступных для упоминания!")
            return

        # Формируем текст с push-тегами
        push_text = " ".join(usernames)
        try:
            await message.edit(push_text)
        except FloodWait as e:
            await asyncio.sleep(e.value)
            await message.edit(push_text)
        except Exception as e:
            await message.edit(f"⚠️ Ошибка при редактировании: {str(e)}")

    except Exception as e:
        logger.error(f"Ошибка в megapush_cmd: {str(e)}")
        await message.edit(f"⚠️ Ошибка: {str(e)}")

def register(app: Client):
    """Регистрирует обработчик команды .мегапуш."""
    app.on_message(filters.create(megapush_filter))(megapush_cmd)