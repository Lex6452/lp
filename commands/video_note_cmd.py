from pyrogram import Client, filters
from pyrogram.types import Message
import os
import unicodedata
import re
import subprocess
from db.db_utils import video_note_exists, save_video_note, delete_video_note, list_video_notes, get_video_note
from utils.filters import template_filter

def normalize_filename(name: str) -> str:
    """Нормализует имя файла, убирая недопустимые символы."""
    name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('ascii')
    name = name.replace(' ', '_')
    name = re.sub(r'[^\w.]', '', name)
    name = re.sub(r'_+', '_', name)
    name = name.strip('_')
    return name or 'video_note'

async def convert_video_to_note(input_path: str, output_path: str) -> bool:
    """Конвертирует видео в видеокружочек с сохранением звука."""
    try:
        # Проверяем наличие аудиодорожки
        has_audio = subprocess.run(
            ["ffprobe", "-i", input_path, "-show_streams", "-select_streams", "a", "-loglevel", "error"],
            capture_output=True
        ).returncode == 0

        command = [
            "ffmpeg",
            "-i", input_path,
            "-vf", "crop=min(iw\\,ih):min(iw\\,ih),scale=512:512",
            "-c:v", "libx264",
            "-profile:v", "baseline",
            "-level", "3.0",
            "-pix_fmt", "yuv420p",
            *(["-c:a", "aac", "-shortest"] if has_audio else ["-an"]),
            "-y",
            output_path
        ]
        
        subprocess.run(command, check=True, timeout=30)
        return os.path.exists(output_path)
    except Exception as e:
        print(f"Ошибка при конвертации: {e}")
        return False

async def convert_to_video_note_cmd(client: Client, message: Message):
    """Конвертирует обычное видео в видеокружочек и сразу отправляет"""
    try:
        if not message.reply_to_message or not message.reply_to_message.video:
            await message.edit("❌ Ответьте на видео для конвертации!")
            return

        user_id = message.from_user.id
        save_dir = "video_notes"
        os.makedirs(save_dir, exist_ok=True)
        
        temp_path = os.path.join(save_dir, f"temp_{user_id}_{message.id}")
        output_path = os.path.join(save_dir, f"converted_{user_id}_{message.id}.mp4")

        # Скачиваем видео
        await client.download_media(message.reply_to_message.video.file_id, temp_path)
        
        # Конвертируем
        if not await convert_video_to_note(temp_path, output_path):
            await message.edit("❌ Ошибка при конвертации!")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return

        # Отправляем результат
        await message.delete()
        await send_video_note_wrapper(client, message.chat.id, output_path)

        # Удаляем временные файлы
        for path in [temp_path, output_path]:
            if os.path.exists(path):
                os.remove(path)
                
    except Exception as e:
        await message.edit(f"⚠️ Ошибка: {str(e)}")
        for path in [temp_path, output_path]:
            if path and os.path.exists(path):
                os.remove(path)

async def add_video_note_cmd(client: Client, message: Message):
    """Сохраняет видеокружочек (со звуком, если есть)"""
    try:
        if not message.reply_to_message or not (message.reply_to_message.video_note or message.reply_to_message.video):
            await message.edit("❌ Ответьте на видеокружочек или видео!")
            return

        video_note_name = message.text.split(maxsplit=1)[1].strip()
        user_id = message.from_user.id

        # Проверка имени
        if not (1 <= len(video_note_name) <= 50):
            await message.edit("❌ Имя должно быть от 1 до 50 символов")
            return
        if any(ord(char) < 32 for char in video_note_name):
            await message.edit("❌ Имя содержит недопустимые символы")
            return
        if await video_note_exists(user_id, video_note_name):
            await message.edit(f"❌ Видеокружочек '{video_note_name}' уже существует!")
            return

        # Подготовка путей
        save_dir = "video_notes"
        os.makedirs(save_dir, exist_ok=True)
        safe_name = normalize_filename(video_note_name)
        temp_path = os.path.join(save_dir, f"temp_{user_id}_{message.id}")
        file_path = os.path.join(save_dir, f"vn_{user_id}_{safe_name}_{message.reply_to_message.id}.mp4")

        # Скачивание и конвертация
        media = message.reply_to_message.video or message.reply_to_message.video_note
        if media.file_size > 50 * 1024 * 1024:
            await message.edit("❌ Файл слишком большой (>50 МБ)")
            return

        await client.download_media(media.file_id, temp_path)
        
        if not await convert_video_to_note(temp_path, file_path):
            await message.edit("❌ Ошибка конвертации!")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return

        # Сохранение в БД
        if await save_video_note(user_id, video_note_name, file_path):
            await message.edit(f"✅ Видеокружочек '{video_note_name}' сохранён!")
        else:
            await message.edit("❌ Ошибка сохранения!")
        
        # Очистка временных файлов
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
    except Exception as e:
        await message.edit(f"⚠️ Ошибка: {str(e)}")
        for path in [temp_path, file_path]:
            if path and os.path.exists(path):
                os.remove(path)

async def send_video_note_wrapper(client: Client, chat_id: int, file_path: str):
    """Обертка для отправки видеокружка с обработкой ошибок"""
    try:
        # Проверяем длительность (не более 60 сек)
        duration = int(float(subprocess.check_output(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", 
             "-of", "default=noprint_wrappers=1:nokey=1", file_path]
        ).decode().strip()))
        
        if duration > 60:
            raise ValueError("Видеокружок должен быть не длиннее 60 секунд")

        await client.send_video_note(
            chat_id=chat_id,
            video_note=file_path,
            duration=duration
        )
        return True
    except Exception as e:
        print(f"Ошибка отправки: {e}")
        return False

async def get_video_note_cmd(client: Client, message: Message):
    """Отправляет сохраненный видеокружочек"""
    try:
        video_note_name = message.text.split(maxsplit=1)[1].strip()
        user_id = message.from_user.id
        file_path = await get_video_note(user_id, video_note_name)

        if not file_path or not os.path.exists(file_path):
            await message.edit(f"❌ Видеокружочек '{video_note_name}' не найден!")
            return

        await message.delete()
        if not await send_video_note_wrapper(client, message.chat.id, file_path):
            await message.reply("❌ Не удалось отправить видеокружочек")
            
    except Exception as e:
        await message.edit(f"⚠️ Ошибка: {str(e)}")

async def delete_video_note_cmd(client: Client, message: Message):
    """Удаляет видеокружочек по имени"""
    try:
        video_note_name = message.text.split(maxsplit=1)[1].strip()
        user_id = message.from_user.id

        if await delete_video_note(user_id, video_note_name):
            await message.edit(f"🗑️ Видеокружочек '{video_note_name}' удалён!")
        else:
            await message.edit(f"❌ Видеокружочек '{video_note_name}' не найден!")
    except Exception as e:
        await message.edit(f"⚠️ Ошибка: {str(e)}")

async def list_video_notes_cmd(client: Client, message: Message):
    """Выводит список всех видеокружочков"""
    try:
        user_id = message.from_user.id
        video_notes = await list_video_notes(user_id)

        if not video_notes:
            await message.edit("📂 У вас нет сохранённых видеокружочков!")
        else:
            video_notes_list = "\n".join(f"{i+1}. {note['name']}" for i, note in enumerate(video_notes))
            await message.edit(f"📂 Ваши видеокружочки:\n\n{video_notes_list}\n\nВсего: {len(video_notes)}")
    except Exception as e:
        await message.edit(f"⚠️ Ошибка: {str(e)}")

def register(app: Client):
    
    app.on_message(template_filter("+кружочек", ignore_case=True) & filters.me)(add_video_note_cmd)
    app.on_message(template_filter("-кружочек", ignore_case=True) & filters.me)(delete_video_note_cmd)
    app.on_message(template_filter("кружочек", ignore_case=True) & filters.me)(list_video_notes_cmd)
    app.on_message(template_filter("кружочки", ignore_case=True) & filters.me)(get_video_note_cmd)
    app.on_message(template_filter("вкруг", ignore_case=True) & filters.me)(convert_to_video_note_cmd)
