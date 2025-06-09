import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from db.db_utils import set_user_prefix

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def set_prefix_cmd(client: Client, message: Message):
    """Устанавливает пользовательский префикс для команд."""
    try:
        if len(message.text.split()) < 2:
            await message.edit("❌ Укажите префикс, например: .префикс к")
            return

        prefix = message.text.split(maxsplit=1)[1].strip()
        if len(prefix) > 1:
            await message.edit("❌ Префикс должен быть одним символом!")
            return

        if not prefix.isprintable() or prefix.isspace():
            await message.edit("❌ Префикс должен быть печатным символом!")
            return

        user_id = message.from_user.id
        if await set_user_prefix(user_id, prefix):
            await message.edit(f"✅ Префикс установлен: '{prefix}'")
            logger.info(f"Префикс '{prefix}' установлен для пользователя {user_id}")
        else:
            await message.edit("❌ Ошибка при установке!")
    except Exception as e:
        logger.error(f"Ошибка при установке префикса: {e}")
        await message.edit(f"⚠️ Ошибка: {str(e)}")

def register(app: Client):
    app.on_message(filters.command("префикс", prefixes=".") & filters.me)(set_prefix_cmd)
    app.on_message(filters.command("преф", prefixes=".") & filters.me)(set_prefix_cmd)