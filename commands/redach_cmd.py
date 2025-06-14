import logging
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from db.db_utils import get_user_prefix, get_edit_text, set_edit_text
from utils.filters import simple_cmd_filter

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def set_edit_text_cmd(client: Client, message: Message):
    try:
        prefix = await get_user_prefix(message.from_user.id)
        cmd_text = message.text.strip()
        logger.info(f"Обработка команды: {cmd_text}")

        # Формируем ожидаемую команду `(префикс)редач`
        command = f"{prefix} редач"
        
        # Проверяем, начинается ли текст с команды
        if not cmd_text.lower().startswith(command.lower()):
            current_text = await get_edit_text(message.from_user.id)
            await message.edit(f"❌ Укажите текст для редактирования, например: `{prefix} редач тут ничего не было`\nТекущий текст: `{current_text}`")
            return

        # Извлекаем текст после команды
        new_text = cmd_text[len(command):].strip()
        logger.info(f"Извлеченный текст: '{new_text}'")

        # Проверяем, указан ли текст
        if not new_text:
            current_text = await get_edit_text(message.from_user.id)
            await message.edit(f"❌ Укажите текст для редактирования, например: `{prefix} редач тут ничего не было`\nТекущий текст: `{current_text}`")
            return

        # Сохраняем текст в базу
        if await set_edit_text(message.from_user.id, new_text):
            await message.edit(f"✅ Текст для редактирования установлен: `{new_text}`")
            logger.info(f"Установлен edit_text='{new_text}' для user_id={message.from_user.id}")
        else:
            await message.edit("❌ Ошибка при сохранении текста!")
            logger.error(f"Ошибка при сохранении edit_text для user_id={message.from_user.id}")

    except Exception as e:
        await message.edit(f"⚠️ Ошибка: {str(e)}")
        logger.error(f"Ошибка в set_edit_text_cmd: {e}")

def register(app: Client):
    app.on_message(simple_cmd_filter("редач", ignore_case=True) & filters.me)(set_edit_text_cmd)