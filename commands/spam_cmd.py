import logging
import asyncio
import re
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.handlers import MessageHandler
from db.db_utils import get_user_prefix
from utils.filters import spam_cmd_filter

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def spam_command(client: Client, message: Message):
    try:
        cmd_text = message.text.strip()
        user_id = message.from_user.id
        chat_id = message.chat.id
        prefix = await get_user_prefix(user_id)
        logger.info(f"Обработка команды спама: '{cmd_text}' для user_id={user_id}, префикс: '{prefix}'")

        # Разбиваем текст на строки
        lines = cmd_text.split('\n')
        first_line = lines[0].strip()

        # Проверяем формат команды: (префикс) спам <количество> [текст]
        command_match = re.match(f"^{re.escape(prefix)}\\s+спам\\s+(\\d+)(?:\\s+(.+))?$", first_line, re.IGNORECASE)
        if not command_match:
            await message.edit(f"❌ Укажите количество сообщений: `{prefix} спам 10 [текст]`")
            logger.debug(f"Некорректный формат команды: '{first_line}', ожидается: '{prefix} спам <число> [текст]'")
            return

        count = int(command_match.group(1))
        spam_text = command_match.group(2).strip() if command_match.group(2) else None

        if count <= 0:
            await message.edit(f"❌ Количество должно быть больше 0")
            return
        if count > 50:  # Ограничение для предотвращения злоупотребления
            await message.edit(f"❌ Максимальное количество сообщений: 50")
            return

        # Проверяем многострочный текст
        if not spam_text and len(lines) > 1:
            spam_text = '\n'.join(lines[1:]).strip()
            logger.debug(f"Получен многострочный текст спама: '{spam_text}'")

        # Если текст не указан, ожидаем следующее сообщение
        if not spam_text:
            await message.edit(f"✍️ Введите текст для спама (одно сообщение):")
            logger.debug(f"Ожидание текста спама для user_id={user_id}")

            text_event = asyncio.Event()
            spam_text_container = [None]

            async def text_handler(_: Client, m: Message):
                if (
                    m.from_user
                    and m.from_user.id == user_id
                    and m.chat.id == chat_id
                    and m.text
                    and not m.text.startswith(prefix)
                ):
                    spam_text_container[0] = m.text.strip()
                    await m.delete()  # Удаляем сообщение с текстом спама
                    text_event.set()
                    logger.debug(f"Получен текст спама: '{spam_text_container[0]}' для user_id={user_id}")
                    return True
                return False

            handler = client.add_handler(
                MessageHandler(
                    text_handler,
                    filters.create(lambda _, __, m: True) & filters.me
                ),
                group=1
            )

            try:
                await asyncio.wait_for(text_event.wait(), timeout=60)
            except asyncio.TimeoutError:
                await message.edit(f"❌ Время ожидания текста истекло (60 секунд)")
                client.remove_handler(handler)
                logger.warning(f"Таймаут ожидания текста спама для user_id={user_id}")
                return
            finally:
                client.remove_handler(handler)

            spam_text = spam_text_container[0]

        if not spam_text:
            await message.edit(f"❌ Текст спама не указан")
            logger.warning(f"Текст спама не получен для user_id={user_id}")
            return

        if len(spam_text) > 2000:
            await message.edit(f"❌ Текст спама слишком длинный (максимум 2000 символов)")
            logger.warning(f"Слишком длинный текст спама для user_id={user_id}")
            return

        await message.delete()  # Удаляем команду

        # Отправляем спам-сообщения
        logger.info(f"Отправка {count} сообщений с текстом '{spam_text}' для user_id={user_id}")
        for i in range(count):
            try:
                await client.send_message(chat_id, spam_text)
                await asyncio.sleep(0.5)  # Пауза 0.5 секунды
            except Exception as e:
                await client.send_message(chat_id, f"⚠️ Ошибка при отправке сообщения {i+1}: {str(e)}")
                logger.error(f"Ошибка при отправке спам-сообщения {i+1} для user_id={user_id}: {e}")
                break

        logger.info(f"Спам завершен: {count} сообщений отправлено для user_id={user_id}")

    except ValueError:
        await message.edit(f"❌ Укажите корректное число")
        logger.error(f"Некорректное число в команде для user_id={user_id}")
    except Exception as e:
        await message.edit(f"⚠️ Ошибка: {str(e)}")
        logger.error(f"Ошибка в spam_command для user_id={user_id}: {e}")

def register(app: Client):
    app.on_message(spam_cmd_filter("спам", ignore_case=True) & filters.me)(spam_command)