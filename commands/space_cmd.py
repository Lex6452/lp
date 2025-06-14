import logging
import re
from datetime import datetime
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message
from db.db_utils import get_user_prefix
from utils.filters import template_filter
from config import NASA_API_KEY

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Настройки API
NASA_APOD_URL = "https://api.nasa.gov/planetary/apod"

async def space_command(client: Client, message: Message):
    """Обрабатывает команду космос: получает Astronomy Picture of the Day от NASA API."""
    try:
        user_id = message.from_user.id
        chat_id = message.chat.id
        prefix = await get_user_prefix(user_id)  # Асинхронный вызов
        logger.info(f"Обработка команды космос для user_id={user_id}, chat_id={chat_id}, префикс: '{prefix}'")

        # Проверяем наличие API-ключа
        if not NASA_API_KEY or NASA_API_KEY == "YOUR_NASA_API_KEY":
            await message.edit_text("❌ API-ключ NASA не настроен. Проверьте config.py")
            logger.error("API-ключ NASA не настроен в config.py")
            return

        # Парсим аргументы команды
        text = message.text.strip()
        parts = text.split()
        if len(parts) < 2:
            await message.edit_text(f"❌ Укажите команду: `{prefix} космос [дата]`")
            return

        args = parts[1:]  # Убираем префикс
        if args[0].lower() != "космос":
            await message.edit_text(f"❌ Неверная команда. Используйте `{prefix} космос [дата]`")
            return

        args = args[1:]  # Убираем "космос"
        date_str = args[0] if args else None

        # Параметры запроса
        params = {"api_key": NASA_API_KEY}
        if date_str:
            # Проверяем формат даты (YYYY-MM-DD)
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
                await message.edit_text("❌ Неверный формат даты. Используйте YYYY-MM-DD")
                return
            try:
                target_date = datetime.strptime(date_str, "%Y-%m-%d")
                now = datetime.now()
                if target_date.date() > now.date():
                    await message.edit_text("❌ Дата не может быть в будущем")
                    return
                params["date"] = date_str
            except ValueError:
                await message.edit_text("❌ Неверная дата")
                return

        # Запрос к NASA API
        async with aiohttp.ClientSession() as session:
            async with session.get(NASA_APOD_URL, params=params) as resp:
                if resp.status == 401:
                    await message.edit_text("❌ Неверный или неактивный API-ключ NASA")
                    logger.error("Ошибка NASA API: Неверный ключ (401)")
                    return
                if resp.status == 404:
                    await message.edit_text("❌ Данные за эту дату недоступны")
                    logger.error(f"Данные APOD за {date_str or 'сегодня'} не найдены (404)")
                    return
                if resp.status != 200:
                    await message.edit_text("❌ Ошибка при получении данных")
                    logger.error(f"Ошибка NASA API: {resp.status}")
                    return
                data = await resp.json()

        # Форматируем ответ
        title = data.get("title", "Без заголовка")
        date = data.get("date", "Неизвестно")
        media_type = data.get("media_type", "unknown")
        url = data.get("url", "")
        explanation = data.get("explanation", "Описание отсутствует")
        # Укорачиваем описание до 500 символов
        if len(explanation) > 500:
            explanation = explanation[:497] + "..."

        media_emoji = "📷" if media_type == "image" else "🎥"
        response = (
            f"🌌 **Космическое фото дня: {title}**\n"
            f"📅 Дата: {date}\n"
            f"{media_emoji} Тип: {'Изображение' if media_type == 'image' else 'Видео'}\n"
            f"🔗 Ссылка: {url}\n"
            f"📖 Описание: {explanation}"
        )

        await message.edit_text(response)
        logger.info(f"APOD за {date} отправлен для user_id={user_id}")

    except Exception as e:
        logger.error(f"Ошибка в space_command для user_id={user_id}: {e}")
        try:
            await message.edit_text("⚠️ Ошибка при получении данных о космосе")
        except Exception as edit_e:
            logger.error(f"Не удалось отредактировать сообщение: {edit_e}")

def register(app: Client):
    """Регистрирует обработчик команды космос."""
    app.on_message(template_filter("космос", ignore_case=True) & filters.me)(space_command)