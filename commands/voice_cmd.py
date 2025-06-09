import logging
import os
import unicodedata
import re
import subprocess
import random
from pyrogram import Client, filters
from pyrogram.types import Message
from db.db_utils import voice_message_exists, save_voice_message, delete_voice_message, list_voice_messages, get_voice_message
from utils.filters import add_voice_filter, delete_voice_filter, get_voice_filter, list_voices_filter

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def normalize_filename(name: str) -> str:
    """Нормализует имя файла, удаляя недопустимые символы."""
    name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('ascii')
    name = name.replace(' ', '_')
    name = re.sub(r'[^\w.]', '', name)
    name = re.sub(r'_+', '_', name)
    name = name.strip('_')
    return name or 'voice'

def generate_unique_filename(save_dir: str, user_id: int) -> str:
    """Генерирует уникальное имя файла для голосового сообщения."""
    while True:
        random_id = random.randint(100000, 999999)  # Случайное 6-значное число
        file_path = os.path.join(save_dir, f"voice_{user_id}_voice_{random_id}.ogg")
        if not os.path.exists(file_path):
            return file_path

async def has_audio_track(file_path: str) -> bool:
    """Проверяет наличие аудиодорожки в файле."""
    try:
        command = [
            'ffprobe',
            '-i', file_path,
            '-show_streams',
            '-select_streams', 'a',
            '-loglevel', 'error'
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        return bool(result.stdout.strip())
    except Exception as e:
        logger.error(f"Ошибка проверки аудиодорожки: {e}")
        return False

async def add_voice_message_cmd(client: Client, message: Message):
    """Сохраняет голосовое сообщение из голоса, аудио или видео."""
    try:
        if not message.reply_to_message or not (message.reply_to_message.voice or message.reply_to_message.audio or message.reply_to_message.video):
            await message.edit("❌ Ответьте на голосовое сообщение, аудиофайл или видео!")
            return

        voice_name = message.text.split(maxsplit=2)[2].strip()
        user_id = message.from_user.id

        if not (1 <= len(voice_name) <= 50):
            await message.edit("❌ Имя должно быть от 1 до 50 символов")
            return

        if any(ord(char) < 32 for char in voice_name):
            await message.edit("❌ Имя содержит недопустимые символы")
            return

        if await voice_message_exists(user_id, voice_name):
            await message.edit(f"❌ Аудиозапись '{voice_name}' уже существует!")
            return

        save_dir = "voice_messages"
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        temp_path = os.path.join(save_dir, f"temp_{user_id}_{message.reply_to_message.id}")
        final_path = generate_unique_filename(save_dir, user_id)

        if message.reply_to_message.voice:
            file_to_download = message.reply_to_message.voice
        elif message.reply_to_message.audio:
            file_to_download = message.reply_to_message.audio
        else:
            file_to_download = message.reply_to_message.video

        if file_to_download.file_size > 50 * 1024 * 1024:
            await message.edit("❌ Файл слишком большой (максимум 50 МБ)")
            return

        # Скачиваем и конвертируем при необходимости
        if message.reply_to_message.voice:
            await client.download_media(file_to_download, final_path)
        else:
            # Скачиваем аудио или видео
            await client.download_media(file_to_download, temp_path)
            # Для видео или аудио конвертируем в OGG
            if message.reply_to_message.video:
                if not await has_audio_track(temp_path):
                    await message.edit("❌ Видео не содержит аудиодорожки!")
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    return
            try:
                command = [
                    'ffmpeg',
                    '-i', temp_path,
                    '-vn',  # Без видео для видео, игнорируется для аудио
                    '-c:a', 'libopus',
                    '-f', 'ogg',
                    '-y',
                    final_path
                ]
                result = subprocess.run(command, check=True, capture_output=True, text=True)
                logger.debug(f"FFmpeg process stdout: {result.stdout}")
            except subprocess.CalledProcessError as e:
                logger.error(f"Ошибка обработки аудио: {e.stderr}")
                await message.edit(f"❌ Ошибка обработки аудио: {e.stderr}")
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                return
            except Exception as e:
                logger.error(f"Общая ошибка обработки аудио: {e}")
                await message.edit("❌ Ошибка обработки аудио!")
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                return

            # Очистка временного файла
            if os.path.exists(temp_path):
                os.remove(temp_path)

        if await save_voice_message(user_id, voice_name, final_path):
            await message.edit(f"✅ Аудиозапись '{voice_name}' сохранена как голосовое сообщение!")
            logger.info(f"Voice message '{voice_name}' saved for user {user_id} at {final_path}")
        else:
            await message.edit("❌ Ошибка при сохранении!")
            if os.path.exists(final_path):
                os.remove(final_path)
    except Exception as e:
        logger.error(f"Ошибка при добавлении голосового сообщения: {e}")
        await message.edit(f"⚠️ Ошибка: {str(e)}")
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.remove(temp_path)
        if 'final_path' in locals() and os.path.exists(final_path):
            os.remove(final_path)

async def delete_voice_message_cmd(client: Client, message: Message):
    """Удаляет голосовое сообщение."""
    try:
        voice_name = message.text.split(maxsplit=2)[2].strip()
        user_id = message.from_user.id

        if await delete_voice_message(user_id, voice_name):
            await message.edit(f"🗑️ Голосовое сообщение '{voice_name}' удалено!")
        else:
            await message.edit(f"❌ Голосовое сообщение '{voice_name}' не найдено!")
    except Exception as e:
        logger.error(f"Ошибка при удалении голосового сообщения: {e}")
        await message.edit(f"⚠️ Ошибка: {str(e)}")

async def list_voice_messages_cmd(client: Client, message: Message):
    """Выводит список голосовых сообщений."""
    try:
        user_id = message.from_user.id
        voices = await list_voice_messages(user_id)

        if not voices:
            await message.edit("📂 У вас нет сохранённых голосовых сообщений!")
        else:
            voices_list = "\n".join(f"{i+1}. {voice['name']}" for i, voice in enumerate(voices))
            await message.edit(f"📂 Ваши голосовые сообщения:\n\n{voices_list}\n\nВсего: {len(voices)}")
    except Exception as e:
        logger.error(f"Ошибка при выводе списка голосовых сообщений: {e}")
        await message.edit(f"⚠️ Ошибка: {str(e)}")

async def get_voice_message_cmd(client: Client, message: Message):
    """Отправляет голосовое сообщение по имени."""
    try:
        voice_name = message.text.split(maxsplit=2)[2].strip()
        user_id = message.from_user.id
        file_path = await get_voice_message(user_id, voice_name)

        if file_path and os.path.exists(file_path):
            await message.delete()
            await client.send_voice(message.chat.id, file_path)
        else:
            await message.edit(f"❌ Голосовое сообщение '{voice_name}' не найдено!")
    except Exception as e:
        logger.error(f"Ошибка при отправке голосового сообщения: {e}")
        await message.edit(f"⚠️ Ошибка: {str(e)}")

def register(app: Client):
    """Регистрирует обработчики команд."""
    app.on_message(filters.create(add_voice_filter))(add_voice_message_cmd)
    app.on_message(filters.create(delete_voice_filter))(delete_voice_message_cmd)
    app.on_message(filters.create(list_voices_filter))(list_voice_messages_cmd)
    app.on_message(filters.create(get_voice_filter))(get_voice_message_cmd)