from pyrogram import filters
from pyrogram.types import Message
from pyrogram import Client

def template_filter(cmd: str):
    async def func(_: Client, __: any, message: Message):
        return (
            message.text is not None and
            message.text.startswith(f".{cmd}") and 
            len(message.text.split()) >= 2 and
            message.from_user and
            message.from_user.is_self
        )
    return filters.create(func)

def simple_cmd_filter(cmd: str):
    async def func(_: Client, __: any, message: Message):
        return (
            message.text is not None and
            message.text.startswith(f".{cmd}") and
            message.from_user and
            message.from_user.is_self
        )
    return filters.create(func)

def add_voice_filter(_: Client, __: any, message: Message):
    return (
        message.text is not None and
        message.text.startswith('.+гс') and
        len(message.text.split()) >= 2 and
        message.from_user and
        message.from_user.is_self
    )

def delete_voice_filter(_: Client, __: any, message: Message):
    return (
        message.text is not None and
        message.text.startswith('.-гс') and
        len(message.text.split()) >= 2 and
        message.from_user and
        message.from_user.is_self
    )

def get_voice_filter(_: Client, __: any, message: Message):
    return (
        message.text is not None and
        message.text.startswith('.гс') and
        len(message.text.split()) >= 2 and
        message.from_user and
        message.from_user.is_self
    )

def list_voices_filter(_: Client, __: any, message: Message):
    return (
        message.text is not None and
        message.text.startswith('.гсы') and
        message.from_user and
        message.from_user.is_self
    )

def add_anim_filter(_: Client, __: any, message: Message):
    return (
        message.text is not None and
        message.text.startswith('.+анимка') and
        len(message.text.split()) >= 2 and
        message.from_user and
        message.from_user.is_self
    )

def delete_anim_filter(_: Client, __: any, message: Message):
    return (
        message.text is not None and
        message.text.startswith('.-анимка') and
        len(message.text.split()) >= 2 and
        message.from_user and
        message.from_user.is_self
    )

def get_anim_filter(_: Client, __: any, message: Message):
    return (
        message.text is not None and
        message.text.startswith('.анимка') and
        len(message.text.split()) >= 2 and
        message.from_user and
        message.from_user.is_self
    )

def list_anims_filter(_: Client, __: any, message: Message):
    return (
        message.text is not None and
        message.text.startswith('.анимки') and
        message.from_user and
        message.from_user.is_self
    )

def add_video_note_filter(_: Client, __: any, message: Message):
    return (
        message.text is not None and
        message.text.startswith('.+кружочек') and
        len(message.text.split()) >= 2 and
        message.from_user and
        message.from_user.is_self
    )

def delete_video_note_filter(_: Client, __: any, message: Message):
    return (
        message.text is not None and
        message.text.startswith('.-кружочек') and
        len(message.text.split()) >= 2 and
        message.from_user and
        message.from_user.is_self
    )

def get_video_note_filter(_: Client, __: any, message: Message):
    return (
        message.text is not None and
        message.text.startswith('.кружочек') and
        len(message.text.split()) >= 2 and
        message.from_user and
        message.from_user.is_self
    )

def list_video_notes_filter(_: Client, __: any, message: Message):
    return (
        message.text is not None and
        message.text.startswith('.кружочки') and
        message.from_user and
        message.from_user.is_self
    )

def add_fake_voice_filter(_: Client, __: any, message: Message):
    return (
        message.text is not None and
        message.text.startswith('.+гсф') and
        message.from_user and
        message.from_user.is_self
    )

def remove_fake_voice_filter(_: Client, __: any, message: Message):
    return (
        message.text is not None and
        message.text.startswith('.-гсф') and
        message.from_user and
        message.from_user.is_self
    )

def add_fake_typing_filter(_: Client, __: any, message: Message):
    return (
        message.text is not None and
        message.text.startswith('.+смсф') and
        message.from_user and
        message.from_user.is_self
    )

def remove_fake_typing_filter(_: Client, __: any, message: Message):
    return (
        message.text is not None and
        message.text.startswith('.-смсф') and
        message.from_user and
        message.from_user.is_self
    )

def list_fake_voice_filter(_: Client, __: any, message: Message):
    return (
        message.text is not None and
        message.text.startswith('.гсф') and
        message.from_user and
        message.from_user.is_self
    )

def list_fake_typing_filter(_: Client, __: any, message: Message):
    return (
        message.text is not None and
        message.text.startswith('.смсф') and
        message.from_user and
        message.from_user.is_self
    )

def enable_online_filter(_: Client, __: any, message: Message):
    return (
        message.text is not None and
        message.text.startswith('.+онлайн') and
        message.from_user and
        message.from_user.is_self
    )

def disable_online_filter(_: Client, __: any, message: Message):
    return (
        message.text is not None and
        message.text.startswith('.-онлайн') and
        message.from_user and
        message.from_user.is_self
    )

def check_online_filter(_: Client, __: any, message: Message):
    return (
        message.text is not None and
        message.text.startswith('.онлайн') and
        message.from_user and
        message.from_user.is_self
    )
