from pyrogram import filters
from pyrogram.types import Message
from pyrogram import Client
from db.db_utils import get_user_prefix, alias_exists

async def get_prefix(message: Message) -> str:
    if message.from_user:
        return await get_user_prefix(message.from_user.id)
    return "."

def template_filter(cmd: str):
    async def func(_: Client, __: any, message: Message):
        prefix = await get_prefix(message)
        return (
            message.text is not None and
            message.text.startswith(f"{prefix} {cmd}") and
            message.from_user and
            message.from_user.is_self
        )
    return filters.create(func)

def simple_cmd_filter(cmd: str):
    async def func(_: Client, __: any, message: Message):
        prefix = await get_prefix(message)
        return (
            message.text is not None and
            message.text == f"{prefix} {cmd}" and
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
    return (
        message.text is not None and
        message.text == f"{prefix} гсы" and
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
