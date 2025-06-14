import logging
import time
import asyncio
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import Message
from utils.filters import simple_cmd_filter

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def ping_command(client: Client, message: Message):
    try:
        # Засекаем время начала обработки
        start_time = time.time()
        
        # Получаем timestamp сообщения (уже в секундах)
        message_timestamp = message.date.timestamp()
        current_timestamp = time.time()
        server_delay = (current_timestamp - message_timestamp) * 1000  # в мс
        
        # Проверяем время ответа API
        api_start = time.time()
        test_msg = await client.send_message(
            chat_id=message.chat.id,
            text="⏳ Измерение ping..."
        )
        api_time = (time.time() - api_start) * 1000  # в мс
        await test_msg.delete()
        
        # Время обработки командой
        processing_time = (time.time() - start_time) * 1000  # в мс
        
        # Формируем ответ
        response = (
            "📊 Результаты ping:\n\n"
            f"• Задержка Telegram: {server_delay:.2f} мс\n"
            f"• Время ответа API: {api_time:.2f} мс\n"
            f"• Время обработки: {processing_time:.2f} мс\n\n"
            f"⏱ Общее время выполнения: {(time.time() - start_time) * 1000:.2f} мс"
        )
        
        await message.edit(response)
        logger.info(f"Проверка ping выполнена для user_id={message.from_user.id}")

    except Exception as e:
        logger.error(f"Ошибка в ping_command: {e}")
        await message.edit("⚠️ Ошибка при проверке ping")

def register(app: Client):
    app.on_message(simple_cmd_filter("пинг", ignore_case=True) & filters.me)(ping_command)