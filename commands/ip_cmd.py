import logging
import ipaddress
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message
from db.db_utils import get_user_prefix
from utils.filters import template_filter

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Настройки API
IPINFO_URL = "https://ipinfo.io/{ip}/geo"

async def ip_command(client: Client, message: Message):
    """Обрабатывает команду ip: получает геолокационные данные об IP-адресе через ipinfo.io."""
    try:
        user_id = message.from_user.id
        chat_id = message.chat.id
        prefix = await get_user_prefix(user_id)  # Асинхронный вызов
        logger.info(f"Обработка команды ip для user_id={user_id}, chat_id={chat_id}, префикс: '{prefix}'")

        # Парсим аргументы команды
        text = message.text.strip()
        parts = text.split()
        if len(parts) < 2:
            await message.edit_text(f"❌ Укажите IP-адрес: `{prefix} ip <IP-адрес>`")
            return

        args = parts[1:]  # Убираем префикс
        if args[0].lower() != "ip":
            await message.edit_text(f"❌ Неверная команда. Используйте `{prefix} ip <IP-адрес>`")
            return

        args = args[1:]  # Убираем "ip"
        if not args:
            await message.edit_text(f"❌ Укажите IP-адрес: `{prefix} ip <IP-адрес>`")
            return

        ip_address = args[0]

        # Валидация IP-адреса
        try:
            ipaddress.ip_address(ip_address)
        except ValueError:
            await message.edit_text("❌ Неверный формат IP-адреса. Используйте IPv4 (например, 192.168.0.1) или IPv6")
            logger.error(f"Неверный IP-адрес: {ip_address}")
            return

        # Запрос к ipinfo.io без API-ключа
        async with aiohttp.ClientSession() as session:
            url = IPINFO_URL.format(ip=ip_address)
            async with session.get(url) as resp:
                if resp.status == 404:
                    await message.edit_text("❌ Данные для этого IP-адреса недоступны")
                    logger.error(f"Данные для IP {ip_address} не найдены (404)")
                    return
                if resp.status == 429:
                    await message.edit_text("❌ Превышен лимит запросов к ipinfo.io")
                    logger.error(f"Превышен лимит запросов для IP {ip_address} (429)")
                    return
                if resp.status != 200:
                    await message.edit_text("❌ Ошибка при получении данных")
                    logger.error(f"Ошибка ipinfo.io API для IP {ip_address}: {resp.status}")
                    return
                data = await resp.json()

        # Форматируем ответ
        ip = data.get("ip", "Неизвестно")
        city = data.get("city", "Неизвестно")
        region = data.get("region", "Неизвестно")
        country = data.get("country", "Неизвестно")
        loc = data.get("loc", "Неизвестно")
        org = data.get("org", "Неизвестно")
        postal = data.get("postal", "Неизвестно")
        timezone = data.get("timezone", "Неизвестно")
        hostname = data.get("hostname", "Неизвестно")

        response = (
            f"🌐 **Информация об IP: {ip}**\n"
            f"🏙️ Город: {city}\n"
            f"🗺️ Регион: {region}\n"
            f"🌍 Страна: {country}\n"
            f"📍 Координаты: {loc}\n"
            f"🏢 Провайдер: {org}\n"
            f"📪 Почтовый индекс: {postal}\n"
            f"⏰ Часовой пояс: {timezone}\n"
            f"💻 Хостнейм: {hostname}"
        )

        await message.edit_text(response)
        logger.info(f"Информация об IP {ip_address} отправлена для user_id={user_id}")

    except Exception as e:
        logger.error(f"Ошибка в ip_command для user_id={user_id}: {e}")
        try:
            await message.edit_text("⚠️ Ошибка при получении данных об IP")
        except Exception as edit_e:
            logger.error(f"Не удалось отредактировать сообщение: {edit_e}")

def register(app: Client):
    app.on_message(template_filter("ip", ignore_case=True) & filters.me)(ip_command)