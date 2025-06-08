import httpx
from datetime import datetime

async def run_remote_speedtest(server_url: str) -> dict | None:
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{server_url.rstrip('/')}/speedtest",
                headers={"User-Agent": "Telegram Speedtest Bot"}
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        print(f"Remote speedtest error: {str(e)}")
        return None

def format_speedtest_results(data: dict, server_name: str = "Unknown") -> str:
    try:
        download = round(data["download"]["bandwidth"] * 8 / 1_000_000, 2)
        upload = round(data["upload"]["bandwidth"] * 8 / 1_000_000, 2)
        ping = round(data["ping"]["latency"], 2)
        isp = data["isp"]
        server = f"{data['server']['name']} ({data['server']['location']})"
        ip = mask_ip(data.get('interface', {}).get('externalIp', 'N/A'))

        return (
            "🚀 <b>Результаты Speedtest</b>\n\n"
            f"<b>🔖 Название сервера:</b> <code>{server_name}</code>\n"
            f"<b>🌐 Сервер теста:</b> {server}\n"
            f"<b>🏠 Провайдер:</b> {isp}\n"
            f"<b>🖥 Внешний IP:</b> <code>{ip}</code>\n\n"
            f"<b>⬇️ Скачивание:</b> <code>{download} Мбит/с</code>\n"
            f"<b>⬆️ Загрузка:</b> <code>{upload} Мбит/с</code>\n"
            f"<b>⏱ Пинг:</b> <code>{ping} мс</code>\n\n"
            f"<i>Тест завершен {datetime.now().strftime('%d.%m.%Y %H:%M')}</i>"
        )
    except KeyError as e:
        print(f"Ошибка форматирования результатов: {e}")
        return "❌ Ошибка при обработке результатов теста"

def mask_ip(ip_address: str) -> str:
    if not ip_address:
        return "N/A"
    parts = ip_address.split('.')
    if len(parts) == 4:
        return f"{parts[0]}.{parts[1]}.***.***"
    return ip_address
