from pyrogram import Client, filters
from pyrogram.types import Message
import os
import unicodedata
import re
from db.db_utils import video_note_exists, save_video_note, delete_video_note, list_video_notes, get_video_note
from utils.filters import add_video_note_filter, delete_video_note_filter, get_video_note_filter, list_video_notes_filter

def normalize_filename(name: str) -> str:
    """Нормализует имя файла, убирая недопустимые символы."""
    name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('ascii')
    name = name.replace(' ', '_')
    name = re.sub(r'[^\w.]', '', name)
    name = re.sub(r'_+', '_', name)
    name = name.strip('_')
    return name or 'video_note'

async def add_video_note_cmd(client: Client, message: Message):
    """Сохраняет видеокружочек из ответа на сообщение под указанным именем."""
    try:
        if not message.reply_to_message or not message.reply_to_message.video_note:
            await message.edit("❌ Ответьте на видеокружочек!")
            return

        video_note_name = message.text.split(maxsplit=2)[2].strip()
        user_id = message.from_user.id

        if not (1 <= len(video_note_name) <= 50):
            await message.edit("❌ Имя должно быть от 1 до 50 символов")
            return

        if any(ord(char) < 32 for char in video_note_name):
            await message.edit("❌ Имя содержит недопустимые управляющие символы")
            return

        if await video_note_exists(user_id, video_note_name):
            await message.edit(f"❌ Видеокружочек '{video_note_name}' уже существует!")
            return

        save_dir = "video_notes"
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        safe_name = normalize_filename(video_note_name)
        file_name = f"video_note_{user_id}_{safe_name}_{message.reply_to_message.id}.mp4"
        file_path = os.path.join(save_dir, file_name)

        if message.reply_to_message.video_note.file_size > 50 * 1024 * 1024:
            await message.edit("❌ Видеокружочек слишком большой (максимум 50 МБ)")
            return

        await client.download_media(message.reply_to_message.video_note.file_id, file_path)

        if await save_video_note(user_id, video_note_name, file_path):
            await message.edit(f"✅ Видеокружочек '{video_note_name}' сохранён!")
        else:
            await message.edit("❌ Ошибка при сохранении!")
            if os.path.exists(file_path):
                os.remove(file_path)
    except Exception as e:
        await message.edit(f"⚠️ Ошибка: {str(e)}")

async def delete_video_note_cmd(client: Client, message: Message):
    """Удаляет видеокружочек по имени."""
    try:
        video_note_name = message.text.split(maxsplit=2)[2].strip()
        user_id = message.from_user.id

        if await delete_video_note(user_id, video_note_name):
            await message.edit(f"🗑️ Видеокружочек '{video_note_name}' удалён!")
        else:
            await message.edit(f"❌ Видеокружочек '{video_note_name}' не найден!")
    except Exception as e:
        await message.edit(f"⚠️ Ошибка: {str(e)}")

async def list_video_notes_cmd(client: Client, message: Message):
    """Выводит список всех сохранённых видеокружочков."""
    try:
        user_id = message.from_user.id
        video_notes = await list_video_notes(user_id)

        if not video_notes:
            await message.edit("📂 У вас нет сохранённых видеокружочков!")
        else:
            video_notes_list = "\n".join(f"{i+1}. {video_note['name']}" for i, video_note in enumerate(video_notes))
            await message.edit(f"📂 Ваши видеокружочки:\n\n{video_notes_list}\n\nВсего: {len(video_notes)}")
    except Exception as e:
        await message.edit(f"⚠️ Ошибка: {str(e)}")

async def get_video_note_cmd(client: Client, message: Message):
    """Отправляет сохранённый видеокружочек по имени."""
    try:
        video_note_name = message.text.split(maxsplit=2)[2].strip()
        user_id = message.from_user.id
        file_path = await get_video_note(user_id, video_note_name)

        if file_path and os.path.exists(file_path):
            await message.delete()
            await client.send_video_note(message.chat.id, file_path)
        else:
            await message.edit(f"❌ Видеокружочек '{video_note_name}' не найден!")
    except Exception as e:
        await message.edit(f"⚠️ Ошибка: {str(e)}")

def register(app: Client):
    """Регистрирует обработчики команд для работы с видеокружочками."""
    app.on_message(filters.create(add_video_note_filter))(add_video_note_cmd)
    app.on_message(filters.create(delete_video_note_filter))(delete_video_note_cmd)
    app.on_message(filters.create(list_video_notes_filter))(list_video_notes_cmd)
    app.on_message(filters.create(get_video_note_filter))(get_video_note_cmd)