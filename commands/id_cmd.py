import logging
import re
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import UserNotParticipant, UsernameNotOccupied, UsernameInvalid
from db.db_utils import get_user_prefix
from utils.filters import template_filter

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def id_command(client: Client, message: Message):
    """Обрабатывает команду ид: возвращает ID чата, пользователя или пользователя по тегу."""
    try:
        user_id = message.from_user.id
        chat_id = message.chat.id
        prefix = await get_user_prefix(user_id)  # Асинхронный вызов
        logger.info(f"Обработка команды ид для user_id={user_id}, chat_id={chat_id}, префикс: '{prefix}'")

        # Парсим команду
        text = message.text.strip()
        parts = text.split()
        if len(parts) < 2 or parts[1].lower() != "ид":
            await message.edit_text(f"❌ Неверная команда. Используйте `{prefix} ид` или `{prefix} ид @username`")
            logger.error(f"Неверная команда: {text}")
            return

        # Определяем сценарий
        response = ""
        if len(parts) == 2 and not message.reply_to_message:
            # Сценарий 1: Без реплая и тега — ID чата и свой ID
            response = (
                f"🆔 **ID чата**: `{chat_id}`\n"
                f"🆔 **Ваш ID**: `{user_id}`\n"
            )
            logger.debug(f"Сценарий 1: ID чата={chat_id}, пользователь={user_id}")

        elif message.reply_to_message:
            # Сценарий 2: С реплаем — ID пользователя из реплая
            if not message.reply_to_message.from_user:
                await message.edit_text("❌ Пользователь в реплае не найден")
                logger.error(f"from_user отсутствует в reply_to_message для user_id={user_id}")
                return
            target_user_id = message.reply_to_message.from_user.id
            target_username = f"@{message.reply_to_message.from_user.username}" if message.reply_to_message.from_user.username else "Отсутствует"
            response = (
                f"🆔 **ID пользователя**: `{target_user_id}`\n"
                f"🔗 **Username**: {target_username}\n"
            )
            logger.debug(f"Сценарий 2: ID пользователя={target_user_id}, username={target_username}")

        elif len(parts) == 3 and parts[2].startswith("@"):
            # Сценарий 3: С тегом — ID пользователя по username
            username = parts[2]
            if not re.match(r"^@[A-Za-z0-9_]{5,}$", username):
                await message.edit_text(f"❌ Неверный формат тега: {username}")
                logger.error(f"Неверный формат тега: {username}")
                return
            try:
                user = await client.get_users(username)
                response = (
                    f"🆔 **ID пользователя**: `{user.id}`\n"
                    f"🔗 **Username**: @{user.username}\n"
                )
                logger.debug(f"Сценарий 3: ID пользователя={user.id}, username=@{user.username}")
            except UsernameNotOccupied:
                await message.edit_text(f"❌ Пользователь {username} не существует")
                logger.error(f"Username {username} не существует")
                return
            except UsernameInvalid:
                await message.edit_text(f"❌ Неверный тег: {username}")
                logger.error(f"Неверный тег: {username}")
                return
            except UserNotParticipant:
                await message.edit_text(f"❌ Пользователь {username} не участвует в чате")
                logger.error(f"Пользователь {username} не участвует в чате")
                return
            except Exception as e:
                await message.edit_text(f"❌ Ошибка при поиске пользователя: {str(e)}")
                logger.error(f"Ошибка при поиске пользователя {username}: {e}")
                return

        else:
            await message.edit_text(f"❌ Неверный формат. Используйте `{prefix} ид`, `{prefix} ид @username` или ответьте на сообщение")
            logger.error(f"Неверный формат команды: {text}")
            return

        # Отправляем ответ
        await message.edit_text(response.strip())
        logger.info(f"ID отправлены для user_id={user_id}: {response.strip()}")

    except Exception as e:
        logger.error(f"Ошибка в id_command для user_id={user_id}: {e}")
        try:
            await message.edit_text(f"⚠️ Ошибка при обработке команды: {str(e)}")
        except Exception as edit_e:
            logger.error(f"Не удалось отредактировать сообщение: {edit_e}")

def register(app: Client):
    """Регистрирует обработчик команды ид."""
    app.on_message(template_filter("ид", ignore_case=True) & filters.me)(id_command)