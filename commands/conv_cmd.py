import logging
import re
from pyrogram import Client, filters
from pyrogram.types import Message
from db.db_utils import get_user_prefix
from utils.filters import template_filter

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Словари для конвертации раскладки
ENG_TO_RUS = {
    'q': 'й', 'w': 'ц', 'e': 'у', 'r': 'к', 't': 'е', 'y': 'н', 'u': 'г', 'i': 'ш', 'o': 'щ', 'p': 'з',
    '[': 'х', ']': 'ъ', 'a': 'ф', 's': 'ы', 'd': 'в', 'f': 'а', 'g': 'п', 'h': 'р', 'j': 'о', 'k': 'л',
    'l': 'д', ';': 'ж', '\'': 'э', 'z': 'я', 'x': 'ч', 'c': 'с', 'v': 'м', 'b': 'и', 'n': 'т', 'm': 'ь',
    ',': 'б', '.': 'ю', '/': '.', '`': 'ё', 'Q': 'Й', 'W': 'Ц', 'E': 'У', 'R': 'К', 'T': 'Е', 'Y': 'Н',
    'U': 'Г', 'I': 'Ш', 'O': 'Щ', 'P': 'З', '{': 'Х', '}': 'Ъ', 'A': 'Ф', 'S': 'Ы', 'D': 'В', 'F': 'А',
    'G': 'П', 'H': 'Р', 'J': 'О', 'K': 'Л', 'L': 'Д', ':': 'Ж', '"': 'Э', 'Z': 'Я', 'X': 'Ч', 'C': 'С',
    'V': 'М', 'B': 'И', 'N': 'Т', 'M': 'Ь', '<': 'Б', '>': 'Ю', '?': ',', '~': 'Ё'
}

RUS_TO_ENG = {v: k for k, v in ENG_TO_RUS.items()}

def is_english_layout(text: str) -> bool:
    """Определяет, написан ли текст на английской раскладке (для русской)."""
    return bool(re.match(r'^[a-zA-Z0-9\s.,;!?()\[\]{}\'"`~<>/-]*$', text))

def is_russian_layout(text: str) -> bool:
    """Определяет, написан ли текст на русской раскладке."""
    return bool(re.match(r'^[а-яА-ЯёЁ0-9\s.,;!?()\[\]{}\'"`~<>/-]*$', text))

def convert_text(text: str, to_russian: bool) -> str:
    """Конвертирует текст между раскладками."""
    mapping = ENG_TO_RUS if to_russian else RUS_TO_ENG
    return ''.join(mapping.get(char, char) for char in text)

async def find_user_message(client: Client, chat_id: int, user_id: int, reply_to_message_id: int = None) -> Message | None:
    """Ищет последнее сообщение пользователя в чате или ответ на конкретное сообщение."""
    try:
        logger.debug(f"Поиск сообщения для user_id={user_id}, reply_to_message_id={reply_to_message_id}")
        async for msg in client.get_chat_history(chat_id, limit=50):
            if not msg:
                logger.debug("Пустое сообщение в истории")
                continue
            if not hasattr(msg, 'from_user') or not msg.from_user:
                logger.debug(f"Сообщение без from_user: {msg}")
                continue
            if msg.from_user.id == user_id and msg.text:
                if reply_to_message_id:
                    if hasattr(msg, 'reply_to_message') and msg.reply_to_message and hasattr(msg.reply_to_message, 'message_id') and msg.reply_to_message.message_id == reply_to_message_id:
                        logger.debug(f"Найден ответ message_id={getattr(msg, 'message_id', 'unknown')}")
                        return msg
                else:
                    logger.debug(f"Найдено последнее сообщение message_id={getattr(msg, 'message_id', 'unknown')}")
                    return msg
        logger.debug("Сообщение не найдено")
        return None
    except Exception as e:
        logger.error(f"Ошибка при поиске сообщения для user_id={user_id}: {e}")
        return None

async def conv_command(client: Client, message: Message):
    """Обрабатывает команду конв: конвертирует текст сообщения между раскладками."""
    try:
        user_id = message.from_user.id
        chat_id = message.chat.id
        prefix = await get_user_prefix(user_id)  # Асинхронный вызов
        logger.info(f"Обработка команды конв для user_id={user_id}, chat_id={chat_id}, префикс: '{prefix}'")

        # Логируем структуру объекта message
        logger.debug(f"Объект message: {vars(message) if hasattr(message, '__dict__') else str(message)}")

        # Парсим команду
        text = message.text.strip()
        parts = text.split()
        if len(parts) < 2 or parts[1].lower() != "конв":
            await message.edit_text(f"❌ Неверная команда. Используйте `{prefix} конв`")
            logger.error(f"Неверная команда: {text}")
            return

        # Проверяем наличие message_id у команды
        command_message_id = getattr(message, 'message_id', None)
        if command_message_id is None:
            logger.warning(f"Команда не имеет message_id для user_id={user_id}, продолжаем без удаления")
            # Продолжаем обработку, но не будем пытаться удалить команду

        # Определяем сценарий
        target_message = None
        if hasattr(message, 'reply_to_message') and message.reply_to_message:
            # Сценарий 2: Ответ на сообщение третьего лица
            reply_to_message_id = getattr(message.reply_to_message, 'message_id', None)
            if reply_to_message_id is None:
                await message.edit_text("❌ Реплай-сообщение не имеет ID")
                logger.error(f"message.reply_to_message не имеет message_id для user_id={user_id}")
                return
            logger.debug(f"Поиск ответа на message_id={reply_to_message_id}")
            target_message = await find_user_message(client, chat_id, user_id, reply_to_message_id)
            if not target_message:
                await message.edit_text("❌ Ваш ответ на сообщение не найден")
                logger.error(f"Ответ user_id={user_id} на message_id={reply_to_message_id} не найден")
                return
        else:
            # Сценарий 1: Собственное сообщение
            logger.debug(f"Поиск последнего сообщения user_id={user_id}")
            target_message = await find_user_message(client, chat_id, user_id)
            if not target_message:
                await message.edit_text("❌ Ваше предыдущее сообщение не найдено")
                logger.error(f"Предыдущее сообщение user_id={user_id} не найдено")
                return

        # Проверяем, что target_message корректен
        target_message_id = getattr(target_message, 'message_id', None)
        if not target_message or target_message_id is None:
            await message.edit_text("❌ Целевое сообщение недоступно или не имеет ID")
            logger.error(f"target_message некорректен или не имеет message_id для user_id={user_id}")
            return

        # Проверяем наличие текста
        if not target_message.text:
            await message.edit_text("❌ Сообщение не содержит текст для конвертации")
            logger.error(f"Сообщение message_id={target_message_id} не содержит текст")
            return

        # Определяем направление конвертации
        original_text = target_message.text.strip()
        logger.debug(f"Оригинальный текст: {original_text}")
        if is_english_layout(original_text):
            converted_text = convert_text(original_text, to_russian=True)
            logger.debug(f"Конвертация в русскую раскладку: {converted_text}")
        elif is_russian_layout(original_text):
            converted_text = convert_text(original_text, to_russian=False)
            logger.debug(f"Конвертация в английскую раскладку: {converted_text}")
        else:
            await message.edit_text("❌ Невозможно определить раскладку текста")
            logger.error(f"Невозможно определить раскладку для текста: {original_text}")
            return

        # Редактируем целевое сообщение
        try:
            await client.edit_message_text(
                chat_id=chat_id,
                message_id=target_message_id,
                text=converted_text
            )
            logger.info(f"Сообщение message_id={target_message_id} отредактировано: {converted_text}")
        except Exception as e:
            await message.edit_text(f"❌ Ошибка при редактировании сообщения: {str(e)}")
            logger.error(f"Ошибка редактирования message_id={target_message_id}: {e}")
            return

        # Удаляем сообщение с командой, если message_id доступен
        if command_message_id:
            try:
                await message.delete()
                logger.info(f"Команда message_id={command_message_id} удалена")
            except Exception as e:
                logger.error(f"Ошибка удаления команды message_id={command_message_id}: {e}")
        else:
            logger.warning(f"Пропущено удаление команды, так как message_id недоступен")

    except Exception as e:
        logger.error(f"Ошибка в conv_command для user_id={user_id}: {e}")
        try:
            await message.edit_text(f"⚠️ Ошибка при обработке команды: {str(e)}")
        except Exception as edit_e:
            logger.error(f"Не удалось отредактировать сообщение: {edit_e}")

def register(app: Client):
    """Регистрирует обработчик команды конв."""
    app.on_message(template_filter("конв", ignore_case=True) & filters.me)(conv_command)