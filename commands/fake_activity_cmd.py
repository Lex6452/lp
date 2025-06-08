from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ChatAction
from db.db_utils import add_fake_activity, remove_fake_activity, list_fake_activities
from utils.filters import (
    add_fake_voice_filter, remove_fake_voice_filter,
    add_fake_typing_filter, remove_fake_typing_filter,
    list_fake_voice_filter, list_fake_typing_filter
)
import asyncio
from typing import Dict

# Глобальный словарь для хранения задач симуляции активности
fake_activity_tasks: Dict[tuple, asyncio.Task] = {}

async def simulate_activity(client: Client, chat_id: int, action: ChatAction):
    """Циклически отправляет действие в чат, пока задача не будет отменена."""
    try:
        while True:
            await client.send_chat_action(chat_id, action)
            await asyncio.sleep(5)  # Telegram требует обновления действия каждые 5 секунд
    except asyncio.CancelledError:
        pass  # Задача была отменена, завершаем цикл
    except Exception as e:
        print(f"Error in simulate_activity: {e}")

async def start_fake_activity(client: Client, user_id: int, chat_id: int, activity_type: str, action: ChatAction, message: Message):
    """Запускает симуляцию активности и сохраняет её в базе данных."""
    try:
        if (user_id, chat_id, activity_type) in fake_activity_tasks:
            await message.edit(f"❌ {activity_type} уже активна в этом чате!")
            return

        if await add_fake_activity(user_id, chat_id, activity_type):
            task = asyncio.create_task(simulate_activity(client, chat_id, action))
            fake_activity_tasks[(user_id, chat_id, activity_type)] = task
            await message.edit(f"✅ {activity_type} включена в этом чате!")
        else:
            await message.edit(f"❌ Ошибка при включении {activity_type}!")
    except Exception as e:
        await message.edit(f"⚠️ Ошибка: {str(e)}")

async def stop_fake_activity(client: Client, user_id: int, chat_id: int, activity_type: str, message: Message):
    """Останавливает симуляцию активности и удаляет её из базы данных."""
    try:
        key = (user_id, chat_id, activity_type)
        if key not in fake_activity_tasks:
            await message.edit(f"❌ {activity_type} не активна в этом чате!")
            return

        if await remove_fake_activity(user_id, chat_id, activity_type):
            task = fake_activity_tasks.pop(key)
            task.cancel()  # Отменяем задачу
            await message.edit(f"✅ {activity_type} отключена в этом чате!")
        else:
            await message.edit(f"❌ Ошибка при отключении {activity_type}!")
    except Exception as e:
        await message.edit(f"⚠️ Ошибка: {str(e)}")

async def add_fake_voice_cmd(client: Client, message: Message):
    """Включает симуляцию записи голосового сообщения."""
    user_id = message.from_user.id
    chat_id = message.chat.id
    await start_fake_activity(client, user_id, chat_id, "Голосовое сообщение", ChatAction.RECORD_AUDIO, message)

async def remove_fake_voice_cmd(client: Client, message: Message):
    """Отключает симуляцию записи голосового сообщения."""
    user_id = message.from_user.id
    chat_id = message.chat.id
    await stop_fake_activity(client, user_id, chat_id, "Голосовое сообщение", message)

async def add_fake_typing_cmd(client: Client, message: Message):
    """Включает симуляцию набора текста."""
    user_id = message.from_user.id
    chat_id = message.chat.id
    await start_fake_activity(client, user_id, chat_id, "Набор текста", ChatAction.TYPING, message)

async def remove_fake_typing_cmd(client: Client, message: Message):
    """Отключает симуляцию набора текста."""
    user_id = message.from_user.id
    chat_id = message.chat.id
    await stop_fake_activity(client, user_id, chat_id, "Набор текста", message)

async def list_fake_voice_cmd(client: Client, message: Message):
    """Выводит список чатов с активной симуляцией голосового сообщения."""
    try:
        user_id = message.from_user.id
        activities = await list_fake_activities(user_id, "Голосовое сообщение")
        if not activities:
            await message.edit("📂 Нет чатов с активной симуляцией голосового сообщения!")
        else:
            chat_list = []
            for i, activity in enumerate(activities, 1):
                chat_id = activity["chat_id"]
                try:
                    chat = await client.get_chat(chat_id)
                    chat_name = chat.title or chat.first_name or f"Чат {chat_id}"
                except:
                    chat_name = f"Чат {chat_id} (недоступен)"
                chat_list.append(f"{i}. {chat_name} (ID: {chat_id})")
            chat_text = "\n".join(chat_list)
            await message.edit(f"📂 Чаты с активной симуляцией голосового сообщения:\n\n{chat_text}\n\nВсего: {len(activities)}")
    except Exception as e:
        await message.edit(f"⚠️ Ошибка: {str(e)}")

async def list_fake_typing_cmd(client: Client, message: Message):
    """Выводит список чатов с активной симуляцией набора текста."""
    try:
        user_id = message.from_user.id
        activities = await list_fake_activities(user_id, "Набор текста")
        if not activities:
            await message.edit("📂 Нет чатов с активной симуляцией набора текста!")
        else:
            chat_list = []
            for i, activity in enumerate(activities, 1):
                chat_id = activity["chat_id"]
                try:
                    chat = await client.get_chat(chat_id)
                    chat_name = chat.title or chat.first_name or f"Чат {chat_id}"
                except:
                    chat_name = f"Чат {chat_id} (недоступен)"
                chat_list.append(f"{i}. {chat_name} (ID: {chat_id})")
            chat_text = "\n".join(chat_list)
            await message.edit(f"📂 Чаты с активной симуляцией набора текста:\n\n{chat_text}\n\nВсего: {len(activities)}")
    except Exception as e:
        await message.edit(f"⚠️ Ошибка: {str(e)}")

def register(app: Client):
    """Регистрирует обработчики команд для симуляции активности."""
    app.on_message(filters.create(add_fake_voice_filter))(add_fake_voice_cmd)
    app.on_message(filters.create(remove_fake_voice_filter))(remove_fake_voice_cmd)
    app.on_message(filters.create(add_fake_typing_filter))(add_fake_typing_cmd)
    app.on_message(filters.create(remove_fake_typing_filter))(remove_fake_typing_cmd)
    app.on_message(filters.create(list_fake_voice_filter))(list_fake_voice_cmd)
    app.on_message(filters.create(list_fake_typing_filter))(list_fake_typing_cmd)