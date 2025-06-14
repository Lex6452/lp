from pyrogram import filters
from pyrogram.types import Message
from pyrogram import Client
from db.db_utils import get_user_prefix, alias_exists, get_delete_cmd
import re
import logging 
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def get_prefix(message: Message) -> str:
    if message.from_user:
        return await get_user_prefix(message.from_user.id)
    return "."

def template_filter(cmd: str, ignore_case: bool = False):
    async def func(_: Client, __: any, message: Message):
        prefix = await get_prefix(message)
        if message.text is None:
            return False
        text_to_check = message.text.lower() if ignore_case else message.text
        cmd_to_check = f"{prefix} {cmd}".lower() if ignore_case else f"{prefix} {cmd}"
        return (
            text_to_check.startswith(cmd_to_check) and
            message.from_user and
            message.from_user.is_self
        )
    return filters.create(func)

def simple_cmd_filter(cmd: str, ignore_case: bool = False):
    async def func(_: Client, __: any, message: Message):
        prefix = await get_prefix(message)
        if message.text is None:
            return False
        text_to_check = message.text.lower() if ignore_case else message.text
        cmd_to_check = f"{prefix} {cmd}".lower() if ignore_case else f"{prefix} {cmd}"
        return (
            text_to_check.startswith(cmd_to_check) and  # Должно быть startswith
            message.from_user and
            message.from_user.is_self
        )
    return filters.create(func)

def set_cmd_filter(cmd: str):
    async def func(_: Client, __: any, message: Message):
        return (
            message.text is not None and
            message.text == f".{cmd}" and
            message.from_user and
            message.from_user.is_self
        )
    return filters.create(func)

async def add_voice_filter(_: Client, __: any, message: Message):
    prefix = await get_prefix(message)
    return (
        message.text is not None and
        message.text.startswith(f"{prefix} +гс") and
        len(message.text.split()) >= 3 and
        message.reply_to_message and
        (message.reply_to_message.voice or message.reply_to_message.audio or message.reply_to_message.video) and
        message.from_user and
        message.from_user.is_self
    )

async def delete_voice_filter(_: Client, __: any, message: Message):
    prefix = await get_prefix(message)
    return (
        message.text is not None and
        message.text.startswith(f"{prefix} -гс") and
        len(message.text.split()) >= 3 and
        message.from_user and
        message.from_user.is_self
    )

async def get_voice_filter(_: Client, __: any, message: Message):
    prefix = await get_prefix(message)
    return (
        message.text is not None and
        message.text.startswith(f"{prefix} гс") and
        len(message.text.split()) >= 3 and
        message.from_user and
        message.from_user.is_self
    )

async def list_voices_filter(_: Client, __: any, message: Message):
    prefix = await get_prefix(message)
    if message.text is None:
        return False
    text_to_check = message.text.lower()
    cmd_to_check = f"{prefix} гсы".lower()
    return (
        text_to_check.startswith(cmd_to_check) and
        message.from_user and
        message.from_user.is_self
    )

async def add_anim_filter(_: Client, __: any, message: Message):
    prefix = await get_prefix(message)
    return (
        message.text is not None and
        message.text.startswith(f"{prefix} +анимка") and
        len(message.text.split()) >= 3 and
        message.reply_to_message and
        message.reply_to_message.text and
        message.from_user and
        message.from_user.is_self
    )

async def delete_anim_filter(_: Client, __: any, message: Message):
    prefix = await get_prefix(message)
    return (
        message.text is not None and
        message.text.startswith(f"{prefix} -анимка") and
        len(message.text.split()) >= 3 and
        message.from_user and
        message.from_user.is_self
    )

async def get_anim_filter(_: Client, __: any, message: Message):
    prefix = await get_prefix(message)
    return (
        message.text is not None and
        message.text.startswith(f"{prefix} анимка") and
        len(message.text.split()) >= 3 and
        message.from_user and
        message.from_user.is_self
    )

async def list_anims_filter(_: Client, __: any, message: Message):
    prefix = await get_prefix(message)
    return (
        message.text is not None and
        message.text == f"{prefix} анимки" and
        message.from_user and
        message.from_user.is_self
    )

async def add_video_note_filter(_: Client, __: any, message: Message):
    prefix = await get_prefix(message)
    return (
        message.text is not None and
        message.text.startswith(f"{prefix} +кружочек") and
        len(message.text.split()) >= 3 and
        message.reply_to_message and
        message.reply_to_message.video_note and
        message.from_user and
        message.from_user.is_self
    )

async def delete_video_note_filter(_: Client, __: any, message: Message):
    prefix = await get_prefix(message)
    return (
        message.text is not None and
        message.text.startswith(f"{prefix} -кружочек") and
        len(message.text.split()) >= 3 and
        message.from_user and
        message.from_user.is_self
    )

async def get_video_note_filter(_: Client, __: any, message: Message):
    prefix = await get_prefix(message)
    return (
        message.text is not None and
        message.text.startswith(f"{prefix} кружочек") and
        len(message.text.split()) >= 3 and
        message.from_user and
        message.from_user.is_self
    )

async def list_video_notes_filter(_: Client, __: any, message: Message):
    prefix = await get_prefix(message)
    return (
        message.text is not None and
        message.text == f"{prefix} кружочки" and
        message.from_user and
        message.from_user.is_self
    )

async def add_fake_voice_filter(_: Client, __: any, message: Message):
    prefix = await get_prefix(message)
    return (
        message.text is not None and
        message.text == f"{prefix} +гсф" and
        message.chat and
        message.from_user and
        message.from_user.is_self
    )

async def remove_fake_voice_filter(_: Client, __: any, message: Message):
    prefix = await get_prefix(message)
    return (
        message.text is not None and
        message.text == f"{prefix} -гсф" and
        message.chat and
        message.from_user and
        message.from_user.is_self
    )

async def add_fake_typing_filter(_: Client, __: any, message: Message):
    prefix = await get_prefix(message)
    return (
        message.text is not None and
        message.text == f"{prefix} +смс" and
        message.chat and
        message.from_user and
        message.from_user.is_self
    )

async def remove_fake_typing_filter(_: Client, __: any, message: Message):
    prefix = await get_prefix(message)
    return (
        message.text is not None and
        message.text == f"{prefix} -смс" and
        message.chat and
        message.from_user and
        message.from_user.is_self
    )

async def list_fake_voice_filter(_: Client, __: any, message: Message):
    prefix = await get_prefix(message)
    return (
        message.text is not None and
        message.text == f"{prefix} гсф" and
        message.from_user and
        message.from_user.is_self
    )

async def list_fake_typing_filter(_: Client, __: any, message: Message):
    prefix = await get_prefix(message)
    return (
        message.text is not None and
        message.text == f"{prefix} смс" and
        message.from_user and
        message.from_user.is_self
    )

async def enable_online_filter(_: Client, __: any, message: Message):
    prefix = await get_prefix(message)
    return (
        message.text is not None and
        message.text == f"{prefix} +онлайн" and
        message.from_user and
        message.from_user.is_self
    )

async def disable_online_filter(_: Client, __: any, message: Message):
    prefix = await get_prefix(message)
    return (
        message.text is not None and
        message.text == f"{prefix} -онлайн" and
        message.from_user and
        message.from_user.is_self
    )

async def check_online_filter(_: Client, __: any, message: Message):
    prefix = await get_prefix(message)
    return (
        message.text is not None and
        message.text == f"{prefix} онлайн" and
        message.from_user and
        message.from_user.is_self
    )

async def add_alias_filter(_: Client, __: any, message: Message):
    prefix = await get_prefix(message)
    return (
        message.text is not None and
        message.text.startswith(f"{prefix} +алиас") and
        len(message.text.split()) >= 3 and
        message.from_user and
        message.from_user.is_self
    )

async def delete_alias_filter(_: Client, __: any, message: Message):
    prefix = await get_prefix(message)
    return (
        message.text is not None and
        message.text.startswith(f"{prefix} -алиас") and
        len(message.text.split()) >= 3 and
        message.from_user and
        message.from_user.is_self
    )

async def list_aliases_filter(_: Client, __: any, message: Message):
    prefix = await get_prefix(message)
    return (
        message.text is not None and
        message.text == f"{prefix} алиасы" and
        message.from_user and
        message.from_user.is_self
    )

async def alias_trigger_filter(_: Client, __: any, message: Message):
    if not (message.text and message.from_user and message.from_user.is_self):
        return False
    text = message.text.strip()
    user_id = message.from_user.id
    return await alias_exists(user_id, text)

async def demotivator_filter(_, __, message: Message) -> bool:
    if not message.text:
        return False
    user_id = message.from_user.id
    prefix = await get_user_prefix(user_id)
    return message.text.lower().startswith(f"{prefix} дем")

async def delete_cmd_trigger_filter(_: Client, __: any, message: Message):
    if not (message.text and message.from_user and message.from_user.is_self):
        return False
        
    text = message.text.strip().lower()  # Приводим к нижнему регистру
    user_id = message.from_user.id
    prefix = (await get_user_prefix(user_id)).lower()  # Приводим к нижнему регистру
    
    # Пропускаем команды, начинающиеся с префикса
    if text.startswith(prefix):
        return False
        
    delete_cmd = (await get_delete_cmd(user_id)).lower()  # Приводим к нижнему регистру
    if not delete_cmd:
        logger.warning(f"Пустой delete_cmd для user_id={user_id}")
        return False
        
    logger.debug(f"Проверка команды: {text}, delete_cmd: {delete_cmd}")
    
    # Проверяем точное совпадение или производные форматы
    number_match = re.match(f"^{re.escape(delete_cmd)}\s+(\d+)$", text)
    edit_number_match = re.match(f"^{re.escape(delete_cmd)}-\s+(\d+)$", text)
    return (
        text == delete_cmd or
        re.match(f"^{re.escape(delete_cmd)}\d+$", text) or
        (number_match and number_match.group(1).isdigit()) or
        text == f"{delete_cmd}-" or
        re.match(f"^{re.escape(delete_cmd)}-\d+$", text) or
        (edit_number_match and edit_number_match.group(1).isdigit())
    )

def spam_cmd_filter(cmd: str, ignore_case: bool = False):
    async def func(_: Client, __: any, message: Message):
        prefix = await get_prefix(message)
        if message.text is None:
            return False
        text_to_check = message.text.lower() if ignore_case else message.text
        cmd_to_check = f"{prefix} {cmd}".lower() if ignore_case else f"{prefix} {cmd}"
        return (
            text_to_check.startswith(cmd_to_check) and
            message.from_user and
            message.from_user.is_self
        )
    return filters.create(func)

def add_interval_filter():
    """Фильтр для команды +интервал."""
    async def func(_, client: Client, message: Message):
        if not message.text or not message.from_user:
            logger.debug(f"Фильтр +интервал: нет текста или пользователя, message={message}")
            return False
        prefix = get_prefix(message)  # Синхронный вызов
        pattern = f"^{re.escape(prefix)}\\s*\\+интервал\\s+(\\S+)\\s+(\\d+)$"
        match = re.match(pattern, message.text.strip(), re.IGNORECASE)
        logger.debug(f"Фильтр +интервал: prefix='{prefix}', pattern='{pattern}', text='{message.text.strip()}', match={match}")
        return bool(match)
    return filters.create(func, name="AddIntervalFilter")

def list_intervals_filter():
    """Фильтр для команды интервалы."""
    async def func(_, client: Client, message: Message):
        if not message.text or not message.from_user:
            logger.debug(f"Фильтр интервалы: нет текста или пользователя, message={message}")
            return False
        prefix = get_prefix(message)  # Синхронный вызов
        pattern = f"^{re.escape(prefix)}\\s*интервалы$"
        match = re.match(pattern, message.text.strip(), re.IGNORECASE)
        logger.debug(f"Фильтр интервалы: prefix='{prefix}', pattern='{pattern}', text='{message.text.strip()}', match={match}")
        return bool(match)
    return filters.create(func, name="ListIntervalsFilter")

def delete_interval_filter():
    """Фильтр для команды -интервал."""
    async def func(_, client: Client, message: Message):
        if not message.text or not message.from_user:
            logger.debug(f"Фильтр -интервал: нет текста или пользователя, message={message}")
            return False
        prefix = get_prefix(message)  # Синхронный вызов
        pattern = f"^{re.escape(prefix)}\\s*\\-интервал\\s+(\\S+)$"
        match = re.match(pattern, message.text.strip(), re.IGNORECASE)
        logger.debug(f"Фильтр -интервал: prefix='{prefix}', pattern='{pattern}', text='{message.text.strip()}', match={match}")
        return bool(match)
    return filters.create(func, name="DeleteIntervalFilter")

def command_with_prefix(cmd: str):
    async def func(_, client: Client, message: Message):
        if not message.text and not message.caption:
            return False
        prefix = await get_prefix(message)
        text = message.caption if message.caption else message.text
        return text.startswith(f"{prefix} {cmd}") and message.from_user.is_self
    return filters.create(func)