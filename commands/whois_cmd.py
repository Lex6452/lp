import logging
import re
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message
from db.db_utils import get_user_prefix
from utils.filters import template_filter
from config import API_KEY_WHOIS, API_BASE_URL_WHOIS

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Регулярное выражение для валидации домена
DOMAIN_REGEX = r"^[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9](?:\.[a-zA-Z]{2,})+$"

async def fetch_whois_data(domain: str, api_key: str) -> dict:
    """Получает WHOIS-данные для одного домена через API."""
    async with aiohttp.ClientSession() as session:
        headers = {"x-api-key": api_key}
        url = f"{API_BASE_URL_WHOIS}/whois/{domain}"
        try:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 400:
                    return {"error": "Invalid domain format"}
                elif response.status == 401:
                    return {"error": "Invalid or missing API key"}
                elif response.status == 429:
                    return {"error": "API key request limit exceeded"}
                else:
                    return {"error": f"API error: {response.status}"}
        except aiohttp.ClientError as e:
            logger.error(f"API request error for {domain}: {e}")
            return {"error": "Failed to connect to API"}

async def fetch_batch_whois_data(domains: list[str], api_key: str) -> dict:
    """Получает WHOIS-данные для нескольких доменов через API."""
    async with aiohttp.ClientSession() as session:
        headers = {"x-api-key": api_key}
        url = f"{API_BASE_URL_WHOIS}/whois"
        payload = {"domains": domains}
        try:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 400:
                    return {"error": "Invalid domains or format"}
                elif response.status == 401:
                    return {"error": "Invalid or missing API key"}
                elif response.status == 429:
                    return {"error": "API key request limit exceeded"}
                else:
                    return {"error": f"API error: {response.status}"}
        except aiohttp.ClientError as e:
            logger.error(f"Batch API request error: {e}")
            return {"error": "Failed to connect to API"}

async def format_whois_data(data: dict, domain: str) -> str:
    """Форматирует WHOIS-данные для вывода."""
    if "error" in data:
        return f"🌍 **WHOIS: {domain}**\n❌ {data['error']}\n\n"
    
    # Извлекаем WHOIS-данные
    whois_text = data.get("whois", "Неизвестно")
    ip_address = data.get("ip_address", "Неизвестно")
    source = data.get("source", "unknown")

    # Парсим ключевые поля из WHOIS-данных
    parsed_data = {
        "Domain Name": domain.lower(),
        "Registrar": "Неизвестно",
        "Creation Date": "Неизвестно",
        "Expiration Date": "Неизвестно",
        "Updated Date": "Неизвестно",
        "Domain Status": "Неизвестно",
        "Name Servers": "Неизвестно",
        "Registrant Name": "Неизвестно",
        "Registrant Email": "Неизвестно",
        "Admin Email": "Неизвестно"
    }

    name_servers = []
    statuses = []
    registrant_email = None
    lines = whois_text.splitlines()
    for line in lines:
        line = line.strip()
        # Поддержка стандартного формата WHOIS
        if line.startswith("Domain Name:"):
            parsed_data["Domain Name"] = line.split(":", 1)[1].strip().lower()
        elif line.startswith("Registrar:"):
            parsed_data["Registrar"] = line.split(":", 1)[1].strip()
        elif line.startswith("Creation Date:"):
            parsed_data["Creation Date"] = line.split(":", 1)[1].strip().split("T")[0]
        elif line.startswith("Registry Expiry Date:") or line.startswith("Expiration Date:"):
            parsed_data["Expiration Date"] = line.split(":", 1)[1].strip().split("T")[0]
        elif line.startswith("Updated Date:"):
            parsed_data["Updated Date"] = line.split(":", 1)[1].strip().split("T")[0]
        elif line.startswith("Domain Status:"):
            status = line.split(":", 1)[1].strip()
            if status not in statuses:
                statuses.append(status)
        elif line.startswith("Name Server:"):
            ns = line.split(":", 1)[1].strip().rstrip(".").lower()  # Удаляем завершающую точку
            if ns not in name_servers:
                name_servers.append(ns)
        elif line.startswith("Registrant Name:") or line.startswith("Registrant Organization:"):
            parsed_data["Registrant Name"] = line.split(":", 1)[1].strip()
        elif line.startswith("Registrant Email:"):
            parsed_data["Registrant Email"] = line.split(":", 1)[1].strip()
        elif line.startswith("Admin Email:"):
            parsed_data["Admin Email"] = line.split(":", 1)[1].strip()
        # Поддержка формата TCI (.ru, .su)
        elif line.startswith("domain:"):
            parsed_data["Domain Name"] = line.split(":", 1)[1].strip().lower()
        elif line.startswith("registrar:"):
            parsed_data["Registrar"] = line.split(":", 1)[1].strip()
        elif line.startswith("created:"):
            parsed_data["Creation Date"] = line.split(":", 1)[1].strip().split("T")[0]
        elif line.startswith("paid-till:"):
            parsed_data["Expiration Date"] = line.split(":", 1)[1].strip().split("T")[0]
        elif line.startswith("state:"):
            status = line.split(":", 1)[1].strip()
            if status not in statuses:
                statuses.append(status)
        elif line.startswith("nserver:"):
            ns = line.split(":", 1)[1].strip().rstrip(".").lower()  # Удаляем завершающую точку
            if ns not in name_servers:
                name_servers.append(ns)
        elif line.startswith("person:"):
            parsed_data["Registrant Name"] = line.split(":", 1)[1].strip()
        elif line.startswith("e-mail:"):
            email = line.split(":", 1)[1].strip().split("(")[0].strip()  # Удаляем (transfer) и пробелы
            if not registrant_email:
                registrant_email = email
                parsed_data["Registrant Email"] = email
            parsed_data["Admin Email"] = email  # TCI использует один email для обоих полей

    if name_servers:
        parsed_data["Name Servers"] = ", ".join(name_servers[:3])
    if statuses:
        parsed_data["Domain Status"] = ", ".join(statuses[:3])

    # Форматируем вывод
    output = (
        f"🌍 **WHOIS: {parsed_data['Domain Name']}**\n"
        f"📝 Регистратор: {parsed_data['Registrar']}\n"
        f"📅 Создан: {parsed_data['Creation Date']}\n"
        f"📅 Истекает: {parsed_data['Expiration Date']}\n"
        f"📅 Обновлён: {parsed_data['Updated Date']}\n"
        f"🔒 Статус: {parsed_data['Domain Status']}\n"
        f"🔗 DNS: {parsed_data['Name Servers']}\n"
        f"👤 Владелец: {parsed_data['Registrant Name']}\n"
        f"📧 Email владельца: {parsed_data['Registrant Email']}\n"
        f"📧 Email админа: {parsed_data['Admin Email']}\n"
    )
    if ip_address != "Неизвестно":
        output += f"🌐 IP-адрес: {ip_address}\n"
    output += f"📡 Источник: {source}\n\n"
    return output

async def whois_command(client: Client, message: Message):
    """Обрабатывает команду whois: получает WHOIS-данные через API."""
    try:
        user_id = message.from_user.id
        chat_id = message.chat.id
        prefix = await get_user_prefix(user_id)
        logger.info(f"Обработка команды whois для user_id={user_id}, chat_id={chat_id}, префикс: '{prefix}'")

        # Парсим аргументы команды
        text = message.text.strip()
        parts = text.split()
        if len(parts) < 2:
            await message.edit_text(f"❌ Укажите домен: `{prefix} whois <домен> [<домен> ...]`")
            return

        args = parts[1:]
        if args[0].lower() != "whois":
            await message.edit_text(f"❌ Неверная команда. Используйте `{prefix} whois <домен> [<домен> ...]`")
            return

        domains = args[1:]
        if not domains:
            await message.edit_text(f"❌ Укажите домен: `{prefix} whois <домен> [<домен> ...]`")
            return

        # Валидация доменов
        valid_domains = []
        for domain in domains:
            if re.match(DOMAIN_REGEX, domain):
                valid_domains.append(domain.lower())
            else:
                await message.edit_text(f"❌ Неверный формат домена: {domain}")
                logger.error(f"Неверный домен: {domain}")
                return

        # Обрабатываем домены
        response = ""
        if len(valid_domains) == 1:
            # Одиночный запрос
            data = await fetch_whois_data(valid_domains[0], API_KEY_WHOIS)
            response = await format_whois_data(data, valid_domains[0])
        else:
            # Пакетный запрос
            batch_data = await fetch_batch_whois_data(valid_domains, API_KEY_WHOIS)
            if "error" in batch_data:
                response = f"❌ {batch_data['error']}\n"
            else:
                for result in batch_data.get("results", []):
                    response += await format_whois_data(result, result.get("domain"))

        if not response:
            await message.edit_text("❌ Данные не найдены для указанных доменов")
            return

        # Ограничиваем длину сообщения
        if len(response) > 4000:
            response = response[:3997] + "..."

        await message.edit_text(response.strip())
        logger.info(f"WHOIS-данные для {', '.join(valid_domains)} отправлены для user_id={user_id}")

    except Exception as e:
        logger.error(f"Ошибка в whois_command для user_id={user_id}: {e}")
        try:
            await message.edit_text("⚠️ Ошибка при получении WHOIS-данных")
        except Exception as edit_e:
            logger.error(f"Не удалось отредактировать сообщение: {edit_e}")

def register(app: Client):
    """Регистрирует обработчик команды whois."""
    app.on_message(template_filter("whois", ignore_case=True) & filters.me)(whois_command)