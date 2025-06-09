import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from db.db_utils import get_user_prefix, list_video_notes, list_voice_messages, list_templates
from pyrogram.enums import ParseMode

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def profile_cmd(client: Client, message: Message):
    """Отображает профиль пользователя с информацией об ID, префиксе и сохранённых данных."""
    try:
        user_id = message.from_user.id
        prefix = await get_user_prefix(user_id)
        video_notes = await list_video_notes(user_id)
        voice_messages = await list_voice_messages(user_id)
        templates = await list_templates(user_id)

        profile_text = (
            f"👤 <b>Ваш профиль</b>\n\n"
            f"🆔 <b>User ID</b>: <code>{user_id}</code>\n"
            f"🔣 <b>Префикс</b>: {prefix}\n"
            f"📹 <b>Видеокружочков</b>: {len(video_notes)}\n"
            f"🎙️ <b>Голосовых сообщений</b>: {len(voice_messages)}\n"
            f"📝 <b>Шаблонов</b>: {len(templates)}"
        )

        await message.edit(profile_text, parse_mode=ParseMode.HTML)
        logger.info(f"Профиль отображён для пользователя {user_id}")
    except Exception as e:
        logger.error(f"Ошибка при отображении профиля: {e}")
        await message.edit(f"⚠️ Ошибка: {str(e)}")

def register(app: Client):
    app.on_message(filters.command("профиль", prefixes=".") & filters.me)(profile_cmd)