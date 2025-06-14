import logging
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from db.db_utils import get_user_prefix, get_delete_cmd, set_delete_cmd
from utils.filters import simple_cmd_filter

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Список зарезервированных команд (взято из alias_cmd.py)
RESERVED_COMMANDS = {
    "type", "hack", "speedtest", "+шаб", "шаб", "-шаб", "шабы",
    "+гс", "гс", "-гс", "гсы", "speed", "+speed", "-speed", "+анимка", "анимка",
    "-анимка", "анимки", "+кружочек", "кружочек", "-кружочек", "кружочки", "+гсф",
    "-гсф", "гсф", "+смс", "-смс", "смс", "+онлайн", "-онлайн", "онлайн", "преф",
    "префикс", "профиль", "+алиас", "-алиас", "алиасы", "help", "удалялка"
}

async def set_delete_cmd_cmd(client: Client, message: Message):
    try:
        prefix = await get_user_prefix(message.from_user.id)
        cmd_text = message.text.strip()
        logger.info(f"Начало обработки команды: {cmd_text}")

        # Формируем ожидаемую команду `(префикс)удалялка`
        command = f"{prefix} удалялка"
        if not cmd_text.lower().startswith(command.lower()):
            current_cmd = await get_delete_cmd(message.from_user.id)
            logger.info(f"Неверный формат команды, текущая команда: {current_cmd}")
            await message.edit(f"❌ Укажите новое название команды, например: `{prefix} удалялка гг`\nТекущая команда: `{current_cmd}`")
            return

        # Извлекаем текст после команды
        new_cmd = cmd_text[len(command):].strip()
        logger.info(f"Извлеченное новое имя команды: {new_cmd}")
        if not new_cmd:
            current_cmd = await get_delete_cmd(message.from_user.id)
            logger.info(f"Имя команды не указано, текущая команда: {current_cmd}")
            await message.edit(f"❌ Укажите новое название команды, например: `{prefix} удалялка гг`\nТекущая команда: `{current_cmd}`")
            return

        # Проверка длины и символов
        if not (1 <= len(new_cmd) <= 50):
            logger.info(f"Недопустимая длина команды: {len(new_cmd)}")
            await message.edit("❌ Название команды должно быть от 1 до 50 символов!")
            return
        if any(ord(char) < 32 for char in new_cmd):
            logger.info(f"Обнаружены недопустимые символы в команде: {new_cmd}")
            await message.edit("❌ Название команды содержит недопустимые символы!")
            return

        # Проверка конфликта с зарезервированными командами
        if new_cmd.lower() in RESERVED_COMMANDS:
            logger.info(f"Команда совпадает с зарезервированной: {new_cmd}")
            await message.edit("❌ Название команды не может совпадать с командами бота!")
            return

        # Сохраняем новое название команды
        logger.info(f"Попытка сохранить команду: {new_cmd}")
        if await set_delete_cmd(message.from_user.id, new_cmd):
            await message.edit(f"✅ Команда удаления установлена: `{new_cmd}`\nТеперь используйте `{new_cmd}` и `{new_cmd}-`")
            logger.info(f"Установлен delete_cmd='{new_cmd}' для user_id={message.from_user.id}")
        else:
            await message.edit("❌ Ошибка при сохранении команды!")
            logger.error(f"Ошибка при сохранении delete_cmd для user_id={message.from_user.id}")

    except Exception as e:
        await message.edit(f"⚠️ Ошибка: {str(e)}")
        logger.error(f"Ошибка в set_delete_cmd_cmd: {e}")

def register(app: Client):
    app.on_message(simple_cmd_filter("удалялка", ignore_case=True) & filters.me)(set_delete_cmd_cmd)