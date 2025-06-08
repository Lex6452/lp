from pyrogram import Client, filters
from pyrogram.types import Message
import os
import unicodedata
import re
from db.db_utils import voice_message_exists, save_voice_message, delete_voice_message, list_voice_messages, get_voice_message
from utils.filters import add_voice_filter, delete_voice_filter, get_voice_filter, list_voices_filter

def normalize_filename(name: str) -> str:
    name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('ascii')
    name = name.replace(' ', '_')
    name = re.sub(r'[^\w.]', '', name)
    name = re.sub(r'_+', '_', name)
    name = name.strip('_')
    return name or 'voice'

async def add_voice_message_cmd(client: Client, message: Message):
    try:
        if not message.reply_to_message or not message.reply_to_message.voice:
            await message.edit("❌ Ответьте на голосовое сообщение!")
            return

        voice_name = message.text.split(maxsplit=1)[1].strip()
        user_id = message.from_user.id

        if not (1 <= len(voice_name) <= 50):
            await message.edit("❌ Имя должно быть от 1 до 50 символов")
            return

        if any(ord(char) < 32 for char in voice_name):
            await message.edit("❌ Имя содержит недопустимые управляющие символы")
            return

        if await voice_message_exists(user_id, voice_name):
            await message.edit(f"❌ Голосовое сообщение '{voice_name}' уже существует!")
            return

        save_dir = "voice_messages"
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        safe_name = normalize_filename(voice_name)
        file_name = f"voice_{user_id}_{safe_name}_{message.reply_to_message.id}.ogg"
        file_path = os.path.join(save_dir, file_name)

        if message.reply_to_message.voice.file_size > 50 * 1024 * 1024:
            await message.edit("❌ Голосовое сообщение слишком большое (максимум 50 МБ)")
            return

        await client.download_media(message.reply_to_message.voice.file_id, file_path)

        if await save_voice_message(user_id, voice_name, file_path):
            await message.edit(f"✅ Голосовое сообщение '{voice_name}' сохранено!")
        else:
            await message.edit("❌ Ошибка при сохранении!")
            if os.path.exists(file_path):
                os.remove(file_path)
    except Exception as e:
        await message.edit(f"⚠️ Ошибка: {str(e)}")

async def delete_voice_message_cmd(client: Client, message: Message):
    try:
        voice_name = message.text.split(maxsplit=1)[1].strip()
        user_id = message.from_user.id

        if await delete_voice_message(user_id, voice_name):
            await message.edit(f"🗑️ Голосовое сообщение '{voice_name}' удалено!")
        else:
            await message.edit(f"❌ Голосовое сообщение '{voice_name}' не найдено!")
    except Exception as e:
        await message.edit(f"⚠️ Ошибка: {str(e)}")

async def list_voice_messages_cmd(client: Client, message: Message):
    try:
        user_id = message.from_user.id
        voices = await list_voice_messages(user_id)

        if not voices:
            await message.edit("📂 У вас нет сохранённых голосовых сообщений!")
        else:
            voices_list = "\n".join(f"{i+1}. {voice['name']}" for i, voice in enumerate(voices))
            await message.edit(f"📂 Ваши голосовые сообщения:\n\n{voices_list}\n\nВсего: {len(voices)}")
    except Exception as e:
        await message.edit(f"⚠️ Ошибка: {str(e)}")

async def get_voice_message_cmd(client: Client, message: Message):
    try:
        voice_name = message.text.split(maxsplit=1)[1].strip()
        user_id = message.from_user.id
        file_path = await get_voice_message(user_id, voice_name)

        if file_path and os.path.exists(file_path):
            await message.delete()
            await client.send_voice(message.chat.id, file_path)
        else:
            await message.edit(f"❌ Голосовое сообщение '{voice_name}' не найдено!")
    except Exception as e:
        await message.edit(f"⚠️ Ошибка: {str(e)}")

def register(app: Client):
    app.on_message(filters.create(add_voice_filter))(add_voice_message_cmd)
    app.on_message(filters.create(delete_voice_filter))(delete_voice_message_cmd)
    app.on_message(filters.create(list_voices_filter))(list_voice_messages_cmd)
    app.on_message(filters.create(get_voice_filter))(get_voice_message_cmd)