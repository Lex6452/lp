import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode
from db.db_utils import alias_exists, save_alias, delete_alias, list_aliases, get_alias_command, get_user_prefix
from utils.filters import add_alias_filter, delete_alias_filter, list_aliases_filter, alias_trigger_filter
from commands.voice_cmd import get_voice_message_cmd
from commands.template_cmd import get_template_cmd
from commands.animation_cmd import get_animation_cmd
from commands.video_note_cmd import get_video_note_cmd

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Список зарезервированных команд, чтобы избежать конфликтов
RESERVED_COMMANDS = {
    "type", "hack", "speedtest", "+шаб", "шаб", "-шаб", "шабы", "дд", "дд-",
    "+гс", "гс", "-гс", "гсы", "speed", "+speed", "-speed", "+анимка", "анимка",
    "-анимка", "анимки", "+кружочек", "кружочек", "-кружочек", "кружочки", "+гсф",
    "-гсф", "гсф", "+смс", "-смс", "смс", "+онлайн", "-онлайн", "онлайн", "преф",
    "префикс", "профиль", "+алиас", "-алиас", "алиасы", "help"
}

# Поддерживаемые команды для алиасов
SUPPORTED_COMMANDS = {"гс", "шаб", "анимка", "кружочек"}

async def add_alias_cmd(client: Client, message: Message):
    """Сохраняет новый алиас."""
    try:
        parts = message.text.split(maxsplit=3)
        if len(parts) < 4:
            await message.edit("❌ Формат: <префикс>+алиас <название> <команда>")
            return

        alias_name = parts[2].strip()
        command = parts[3].strip()
        user_id = message.from_user.id
        prefix = await get_user_prefix(user_id)

        # Проверка длины и символов алиаса
        if not (1 <= len(alias_name) <= 50):
            await message.edit("❌ Название алиаса должно быть от 1 до 50 символов!")
            return
        if any(ord(char) < 32 for char in alias_name):
            await message.edit("❌ Название алиаса содержит недопустимые символы!")
            return

        # Проверка конфликта с зарезервированными командами
        if alias_name.lower() in RESERVED_COMMANDS:
            await message.edit("❌ Название алиаса не может совпадать с командами бота!")
            return

        # Проверка, что команда начинается с префикса
        if not command.startswith(f"{prefix} "):
            await message.edit(f"❌ Команда должна начинаться с '{prefix} <команда> <имя>'!")
            return

        # Проверка, что команда — это одна из поддерживаемых
        cmd_parts = command.split()
        if len(cmd_parts) < 3:
            await message.edit(f"❌ Команда должна включать имя, например: '{prefix} <команда> <имя>'!")
            return
        cmd_name = cmd_parts[1].lower()
        if cmd_name not in SUPPORTED_COMMANDS:
            supported_list = ", ".join(f"'{prefix} {cmd}'" for cmd in SUPPORTED_COMMANDS)
            await message.edit(f"❌ Поддерживаются только команды: {supported_list}")
            return

        if await alias_exists(user_id, alias_name):
            await message.edit(f"❌ Алиас '{alias_name}' уже существует!")
            return

        if await save_alias(user_id, alias_name, command):
            await message.edit(f"✅ Алиас '{alias_name}' сохранён для команды: {command}")
            logger.info(f"Алиас '{alias_name}' сохранён для пользователя {user_id}: {command}")
        else:
            await message.edit("❌ Ошибка при сохранении алиаса!")
    except Exception as e:
        logger.error(f"Ошибка при добавлении алиаса: {e}")
        await message.edit(f"⚠️ Ошибка: {str(e)}")

async def delete_alias_cmd(client: Client, message: Message):
    """Удаляет алиас."""
    try:
        parts = message.text.split(maxsplit=2)
        if len(parts) < 3:
            await message.edit("❌ Укажите название алиаса, например: <префикс>-алиас <название>")
            return

        alias_name = parts[2].strip()
        user_id = message.from_user.id

        if await delete_alias(user_id, alias_name):
            await message.edit(f"🗑️ Алиас '{alias_name}' удалён!")
            logger.info(f"Алиас '{alias_name}' удалён для пользователя {user_id}")
        else:
            await message.edit(f"❌ Алиас '{alias_name}' не найден!")
    except Exception as e:
        logger.error(f"Ошибка при удалении алиаса: {e}")
        await message.edit(f"⚠️ Ошибка: {str(e)}")

async def list_aliases_cmd(client: Client, message: Message):
    """Выводит список алиасов пользователя."""
    try:
        user_id = message.from_user.id
        aliases = await list_aliases(user_id)

        if not aliases:
            await message.edit("📂 У вас нет сохранённых алиасов!")
        else:
            aliases_list = "\n".join(
                f"{i+1}. <code>{alias['name']}</code> → {alias['command']}"
                for i, alias in enumerate(aliases)
            )
            await message.edit(
                f"📂 Ваши алиасы:\n\n{aliases_list}\n\nВсего: {len(aliases)}",
                parse_mode=ParseMode.HTML
            )
            logger.info(f"Список алиасов выведен для пользователя {user_id}")
    except Exception as e:
        logger.error(f"Ошибка при выводе списка алиасов: {e}")
        await message.edit(f"⚠️ Ошибка: {str(e)}")

async def trigger_alias_cmd(client: Client, message: Message):
    """Обрабатывает вызов алиаса."""
    try:
        alias_name = message.text.strip()
        user_id = message.from_user.id
        command = await get_alias_command(user_id, alias_name)

        if not command:
            return  # Не алиас, пропускаем

        # Удаляем сообщение с алиасом
        await message.delete()

        # Парсим команду
        cmd_parts = command.split()
        if len(cmd_parts) < 3:
            await client.send_message(
                chat_id=message.chat.id,
                text=f"❌ Неверный формат команды в алиасе: {command}"
            )
            return

        cmd_name = cmd_parts[1].lower()
        # Выбираем соответствующий обработчик
        if cmd_name == "гс":
            fake_message = message
            fake_message.text = command
            fake_message.from_user.id = user_id
            await get_voice_message_cmd(client, fake_message)
        elif cmd_name == "шаб":
            fake_message = message
            fake_message.text = command
            fake_message.from_user.id = user_id
            await get_template_cmd(client, fake_message)
        elif cmd_name == "анимка":
            fake_message = message
            fake_message.text = command
            fake_message.from_user.id = user_id
            await get_animation_cmd(client, fake_message)
        elif cmd_name == "кружочек":
            fake_message = message
            fake_message.text = command
            fake_message.from_user.id = user_id
            await get_video_note_cmd(client, fake_message)
        else:
            supported_list = ", ".join(f"'{cmd}'" for cmd in SUPPORTED_COMMANDS)
            await client.send_message(
                chat_id=message.chat.id,
                text=f"❌ Команда '{cmd_name}' не поддерживается в алиасах. Поддерживаются: {supported_list}"
            )
            return

        logger.info(f"Алиас '{alias_name}' вызвал команду '{command}' для пользователя {user_id}")
    except Exception as e:
        logger.error(f"Ошибка при вызове алиаса: {e}")
        await client.send_message(
            chat_id=message.chat.id,
            text=f"⚠️ Ошибка при вызове алиаса: {str(e)}"
        )

def register(app: Client):
    """Регистрирует обработчики команд."""
    app.on_message(filters.create(add_alias_filter))(add_alias_cmd)
    app.on_message(filters.create(delete_alias_filter))(delete_alias_cmd)
    app.on_message(filters.create(list_aliases_filter))(list_aliases_cmd)
    app.on_message(filters.create(alias_trigger_filter))(trigger_alias_cmd)