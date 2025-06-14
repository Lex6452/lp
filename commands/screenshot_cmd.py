import pyrogram
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.raw.functions.messages import SendScreenshotNotification
from pyrogram.raw.types import InputPeerUser
from pyrogram.enums import ChatType
from utils.filters import simple_cmd_filter
import logging
import time
import asyncio

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def send_screenshot_cmd(client: Client, message: Message):
    try:
        # Проверяем, что message.chat существует
        if not message.chat:
            logger.error(f"Чат не определён: user_id={message.from_user.id}")
            await message.delete()
            return

        # Логируем детали чата
        chat_type = message.chat.type
        user_id = message.from_user.id
        chat_id = message.chat.id
        logger.info(f"Обработка команды скрин: user_id={user_id}, chat_id={chat_id}, chat_type={chat_type}, chat={message.chat}")

        # Проверяем, что чат личный или с ботом
        if chat_type not in [ChatType.PRIVATE, ChatType.BOT]:
            logger.error(f"Некорректный тип чата: {chat_type}")
            await message.delete()
            return

        # Получаем InputPeer для пользователя
        peer = await client.resolve_peer(chat_id)
        logger.info(f"Получен peer: {peer}, type={type(peer)}")
        if not isinstance(peer, InputPeerUser):
            logger.error(f"Некорректный peer: {type(peer)}")
            await message.delete()
            return

        # Указываем reply_to_msg_id, если есть ответ на сообщение
        reply_to_msg_id = message.reply_to_message.id if message.reply_to_message else 0

        # Парсим количество уведомлений
        parts = message.text.strip().split(maxsplit=2)
        count = 1  # По умолчанию 1 уведомление
        if len(parts) > 2:
            try:
                count = int(parts[2])
                if count < 1:
                    logger.error(f"Некорректное количество: {count}")
                    await message.delete()
                    return
                if count > 10:  # Ограничение на максимум 10 уведомлений
                    count = 10
                    logger.info(f"Количество ограничено до 10: user_id={user_id}")
            except ValueError:
                logger.error(f"Некорректный формат количества: {parts[2]}")
                await message.delete()
                return

        # Отправляем уведомления
        for i in range(count):
            # Уникальный random_id для каждого уведомления
            random_id = int(time.time() * 1000) + i
            logger.info(f"Отправка уведомления {i+1}/{count}: peer={peer}, reply_to_msg_id={reply_to_msg_id}, random_id={random_id}")

            # Отправляем уведомление о скриншоте
            await client.invoke(
                SendScreenshotNotification(
                    peer=peer,
                    reply_to_msg_id=reply_to_msg_id,
                    random_id=random_id
                )
            )

            # Задержка 0.5 секунды между уведомлениями (избегаем FloodWait)
            if i < count - 1:
                await asyncio.sleep(0.5)

        # Удаляем сообщение команды
        try:
            await message.delete()
        except pyrogram.errors.Forbidden as e:
            logger.error(f"Нет прав на удаление сообщения: {e}, user_id={user_id}, chat_id={chat_id}")
            pass  # Игнорируем, если нет прав

    except pyrogram.errors.FloodWait as e:
        logger.error(f"FloodWait: ждать {e.x} секунд, user_id={user_id}")
        try:
            await message.delete()
        except pyrogram.errors.Forbidden:
            pass
    except pyrogram.errors.BadRequest as e:
        logger.error(f"BadRequest в send_screenshot_cmd: {e}, user_id={user_id}")
        try:
            await message.delete()
        except pyrogram.errors.Forbidden:
            pass
    except Exception as e:
        logger.error(f"Ошибка в send_screenshot_cmd: {e}, user_id={user_id}")
        try:
            await message.delete()
        except pyrogram.errors.Forbidden:
            pass

def register(app: Client):
    app.on_message(simple_cmd_filter("скрин", ignore_case=True) & filters.me)(send_screenshot_cmd)