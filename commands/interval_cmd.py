import logging
import asyncio
import re
from typing import Dict, List
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.handlers import MessageHandler
from pyrogram import errors as pyrogram_errors
from db.db_utils import get_user_prefix, save_interval, count_intervals, list_intervals, delete_interval
from utils.filters import simple_cmd_filter

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Словарь для хранения активных задач интервалов
active_intervals: Dict[str, asyncio.Task] = {}

async def interval_task(client: Client, user_id: int, interval_name: str, 
                       chat_id: int, interval_text: str, interval_minutes: int):
    """Фоновая задача для отправки сообщений по интервалу"""
    try:
        while True:
            try:
                await client.send_message(chat_id, interval_text)
                logger.info(f"Отправлено интервальное сообщение '{interval_name}' в chat_id={chat_id}")
            except pyrogram_errors.ChatWriteForbidden:
                logger.warning(f"Нет прав для отправки в chat_id={chat_id}")
                break
            except pyrogram_errors.ChatNotFound:
                logger.warning(f"Чат {chat_id} не найден")
                break
            except Exception as e:
                logger.error(f"Ошибка отправки в chat_id={chat_id}: {str(e)}")
                # Продолжаем попытки, если это не фатальная ошибка
                if isinstance(e, (pyrogram_errors.ChatWriteForbidden, 
                                pyrogram_errors.ChatNotFound)):
                    break
            
            await asyncio.sleep(interval_minutes * 60)
            
    except asyncio.CancelledError:
        logger.info(f"Интервал '{interval_name}' отменен")
    except Exception as e:
        logger.error(f"Критическая ошибка в интервале '{interval_name}': {str(e)}")

async def add_interval_command(client: Client, message: Message):
    """Обработчик команды добавления интервала"""
    try:
        user_id = message.from_user.id
        chat_id = message.chat.id
        prefix = await get_user_prefix(user_id)
        
        # Разбиваем сообщение на строки
        lines = message.text.split('\n')
        if len(lines) < 2:
            await message.edit(f"❌ Укажите текст интервала с новой строки\nПример:\n{prefix} +интервал тест 10\nТекст сообщения")
            return

        # Парсим первую строку
        args = lines[0].strip().split()
        if len(args) < 4:
            await message.edit(f"❌ Формат: {prefix} +интервал название время_в_минутах")
            return

        interval_name = args[2]
        try:
            interval_minutes = int(args[3])
            if interval_minutes <= 0:
                raise ValueError
        except ValueError:
            await message.edit("❌ Время должно быть числом больше 0")
            return

        # Получаем текст интервала (все что после первой строки)
        interval_text = '\n'.join(lines[1:]).strip()
        if not interval_text:
            await message.edit("❌ Текст интервала не может быть пустым")
            return

        # Проверяем лимит интервалов
        if await count_intervals(user_id) >= 5:
            await message.edit("❌ Лимит интервалов (5)")
            return

        # Сохраняем в БД
        if not await save_interval(user_id, interval_name, chat_id, interval_minutes, interval_text):
            await message.edit("❌ Ошибка сохранения (возможно, имя занято)")
            return

        # Запускаем задачу
        task_key = f"{user_id}:{interval_name}"
        if task_key in active_intervals:
            active_intervals[task_key].cancel()
            
        active_intervals[task_key] = asyncio.create_task(
            interval_task(client, user_id, interval_name, chat_id, interval_text, interval_minutes)
        )

        await message.edit(f"✅ Интервал '{interval_name}' создан (каждые {interval_minutes} мин)")
        logger.info(f"Создан интервал '{interval_name}' для user_id={user_id}")

    except Exception as e:
        logger.error(f"Ошибка в add_interval_command: {str(e)}")
        await message.edit(f"⚠️ Ошибка: {str(e)}")

async def list_intervals_command(client: Client, message: Message):
    """Обработчик команды списка интервалов"""
    try:
        user_id = message.from_user.id
        intervals = await list_intervals(user_id)
        
        if not intervals:
            await message.edit("📋 Нет активных интервалов")
            return

        response = ["📋 Ваши интервалы:"]
        for i, interval in enumerate(intervals, 1):
            try:
                chat = await client.get_chat(interval['chat_id'])
                chat_info = chat.title or f"ID: {interval['chat_id']}"
            except:
                chat_info = f"ID: {interval['chat_id']} (недоступен)"
                
            response.append(
                f"{i}. {interval['interval_name']} - каждые {interval['interval_minutes']} мин\n"
                f"   Чат: {chat_info}\n"
                f"   Текст: {interval['interval_text'][:50]}..."
            )

        await message.edit("\n\n".join(response))
        
    except Exception as e:
        logger.error(f"Ошибка в list_intervals_command: {str(e)}")
        await message.edit(f"⚠️ Ошибка: {str(e)}")

async def delete_interval_command(client: Client, message: Message):
    """Обработчик команды удаления интервала"""
    try:
        user_id = message.from_user.id
        args = message.text.strip().split()
        
        if len(args) < 3:
            prefix = await get_user_prefix(user_id)
            await message.edit(f"❌ Формат: {prefix} -интервал название")
            return

        interval_name = args[2]
        
        # Удаляем из БД
        if not await delete_interval(user_id, interval_name):
            await message.edit(f"❌ Интервал '{interval_name}' не найден")
            return

        # Останавливаем задачу
        task_key = f"{user_id}:{interval_name}"
        if task_key in active_intervals:
            active_intervals[task_key].cancel()
            del active_intervals[task_key]

        await message.edit(f"✅ Интервал '{interval_name}' удален")
        logger.info(f"Удален интервал '{interval_name}' для user_id={user_id}")

    except Exception as e:
        logger.error(f"Ошибка в delete_interval_command: {str(e)}")
        await message.edit(f"⚠️ Ошибка: {str(e)}")

def register(app: Client):
    """Регистрация обработчиков команд"""
    app.on_message(simple_cmd_filter("+интервал", ignore_case=True) & filters.me)(add_interval_command)
    app.on_message(simple_cmd_filter("интервалы", ignore_case=True) & filters.me)(list_intervals_command)
    app.on_message(simple_cmd_filter("-интервал", ignore_case=True) & filters.me)(delete_interval_command)