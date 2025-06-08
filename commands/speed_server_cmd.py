from pyrogram import Client, filters
from pyrogram.types import Message
from db.db_utils import list_speed_servers, get_speed_server, remove_speed_server, add_speed_server
from utils.speedtest_utils import run_remote_speedtest, format_speedtest_results, mask_ip
import asyncio
from urllib.parse import urlparse
import re

def extract_masked_ip_from_url(url: str) -> str:
    """Извлекает IP из URL и маскирует его, сохраняя порт."""
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        port = parsed.port if parsed.port else ""
        # Проверяем, является ли hostname IP-адресом
        if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", hostname):
            masked_ip = mask_ip(hostname)
            return f"{parsed.scheme}://{masked_ip}{':' + str(port) if port else ''}"
        return url  # Если не IP, возвращаем исходный URL
    except Exception:
        return url  # В случае ошибки возвращаем исходный URL

async def list_speed_servers_cmd(client: Client, message: Message):
    """Выводит список серверов для тестирования скорости с замаскированными IP."""
    try:
        servers = await list_speed_servers()
        if not servers:
            await message.edit("📂 Нет сохранённых серверов!")
        else:
            servers_list = "\n".join(
                f"{server['id']}. {server['name']} ({extract_masked_ip_from_url(server['url'])})"
                for server in servers
            )
            await message.edit(f"📂 Список серверов:\n\n{servers_list}\n\nВсего: {len(servers)}")
    except Exception as e:
        await message.edit(f"⚠️ Ошибка: {str(e)}")

async def speedtest_server_cmd(client: Client, message: Message):
    """Запускает тест скорости на указанном сервере по его ID."""
    try:
        if len(message.command) < 2:
            await message.edit("❌ Укажите ID сервера: `.speed 1`")
            return

        server_id = message.text.split()[1]
        try:
            server_id = int(server_id)
        except ValueError:
            await message.edit("❌ ID сервера должен быть числом!")
            return

        server = await get_speed_server(server_id)
        if not server:
            await message.edit(f"❌ Сервер с ID {server_id} не найден!")
            return

        msg = await message.edit(f"⏳ Запуск теста скорости на сервере {server['name']}...")
        data = await run_remote_speedtest(server['url'])
        
        if not data:
            await msg.edit(f"❌ Ошибка при выполнении теста скорости на сервере {server['name']}")
            return

        result_text = format_speedtest_results(data, server['name'])
        await msg.edit(result_text)
    except Exception as e:
        await message.edit(f"⚠️ Ошибка: {str(e)}")

async def remove_speed_server_cmd(client: Client, message: Message):
    """Удаляет сервер из базы данных по его ID."""
    try:
        if len(message.command) < 2:
            await message.edit("❌ Укажите ID сервера: `.-speed 1`")
            return

        server_id = message.text.split()[1]
        try:
            server_id = int(server_id)
        except ValueError:
            await message.edit("❌ ID сервера должен быть числом!")
            return

        server = await get_speed_server(server_id)
        if not server:
            await message.edit(f"❌ Сервер с ID {server_id} не найден!")
            return

        if await remove_speed_server(server['name']):
            await message.edit(f"🗑️ Сервер '{server['name']}' удалён!")
        else:
            await message.edit(f"❌ Ошибка при удалении сервера '{server['name']}'!")
    except Exception as e:
        await message.edit(f"⚠️ Ошибка: {str(e)}")

async def add_speed_server_cmd(client: Client, message: Message):
    """Добавляет сервер в базу данных по имени и URL."""
    try:
        if len(message.command) < 3:
            await message.edit("❌ Укажите название и URL сервера: `.+speed имя http://example.com`")
            return

        parts = message.text.split(maxsplit=2)
        name, url = parts[1], parts[2]

        if await add_speed_server(name, url):
            await message.edit(f"✅ Сервер '{name}' добавлен!")
        else:
            await message.edit(f"❌ Ошибка при добавлении сервера '{name}'!")
    except Exception as e:
        await message.edit(f"⚠️ Ошибка: {str(e)}")

def register(app: Client):
    """Регистрирует обработчики команд для работы с серверами тестирования скорости."""
    app.on_message(filters.command("speed", prefixes=".") & filters.me & ~filters.regex(r"^\.speed\s+\d+$"))(list_speed_servers_cmd)
    app.on_message(filters.command("speed", prefixes=".") & filters.me & filters.regex(r"^\.speed\s+\d+$"))(speedtest_server_cmd)
    app.on_message(filters.command("-speed", prefixes=".") & filters.me)(remove_speed_server_cmd)
    app.on_message(filters.command("+speed", prefixes=".") & filters.me)(add_speed_server_cmd)