from pyrogram import Client, filters
from pyrogram.types import Message
import asyncio
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Глобальная переменная для состояния вечного онлайна
online_task = None
is_online_enabled = False

async def keep_online(client: Client):
    """Фоновая задача для поддержания статуса онлайн."""
    global is_online_enabled
    while is_online_enabled:
        try:
            await client.get_me()  # Отправляем запрос, чтобы обновить статус
            logger.info("Отправлен запрос для поддержания статуса онлайн")
            await asyncio.sleep(300)  # Ждём 5 минут
        except Exception as e:
            logger.error(f"Ошибка при поддержании онлайна: {str(e)}")
            await asyncio.sleep(60)  # Ждём 1 минуту перед повтором

async def enable_online(client: Client, message: Message):
    """Включает вечный онлайн."""
    global online_task, is_online_enabled
    try:
        if is_online_enabled:
            await message.edit("✅ Вечный онлайн уже включён!")
            return

        is_online_enabled = True
        online_task = asyncio.create_task(keep_online(client))
        await message.edit("✅ Вечный онлайн включён!")
        logger.info("Вечный онлайн включён")
    except Exception as e:
        logger.error(f"Ошибка при включении онлайна: {str(e)}")
        await message.edit(f"⚠️ Ошибка: {str(e)}")

async def disable_online(client: Client, message: Message):
    """Отключает вечный онлайн."""
    global online_task, is_online_enabled
    try:
        if not is_online_enabled:
            await message.edit("❌ Вечный онлайн уже отключён!")
            return

        is_online_enabled = False
        if online_task:
            online_task.cancel()
            online_task = None
        await message.edit("✅ Вечный онлайн отключён!")
        logger.info("Вечный онлайн отключён")
    except Exception as e:
        logger.error(f"Ошибка при отключении онлайна: {str(e)}")
        await message.edit(f"⚠️ Ошибка: {str(e)}")

async def check_online(client: Client, message: Message):
    """Проверяет статус вечного онлайна."""
    try:
        status = "включён" if is_online_enabled else "отключён"
        await message.edit(f"ℹ️ Вечный онлайн: {status}")
    except Exception as e:
        logger.error(f"Ошибка при проверке онлайна: {str(e)}")
        await message.edit(f"⚠️ Ошибка: {str(e)}")

def register(app: Client):
    """Регистрирует обработчики команд для вечного онлайна."""
    app.on_message(filters.create(lambda _, __, m: m.text and m.text.startswith('.+онлайн') and m.from_user and m.from_user.is_self))(enable_online)
    app.on_message(filters.create(lambda _, __, m: m.text and m.text.startswith('.-онлайн') and m.from_user and m.from_user.is_self))(disable_online)
    app.on_message(filters.create(lambda _, __, m: m.text and m.text.startswith('.онлайн') and m.from_user and m.from_user.is_self))(check_online)