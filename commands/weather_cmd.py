import logging
import re
import aiohttp
from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.types import Message
from db.db_utils import get_user_prefix
from utils.filters import template_filter
from config import OPENWEATHERMAP_API_KEY

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Настройки API
WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
GEOCODING_URL = "https://api.openweathermap.org/geo/1.0/direct"
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

# Словарь для преобразования кодов погоды Open-Meteo в описания и emoji
WEATHER_CODE_MAP = {
    0: ("Ясно", "☀️"),
    1: ("В основном ясно", "⛅"),
    2: ("Переменная облачность", "⛅"),
    3: ("Пасмурно", "☁️"),
    45: ("Туман", "🌫️"),
    48: ("Изморозь", "🌫️"),
    51: ("Лёгкая морось", "🌧️"),
    53: ("Морось", "🌧️"),
    55: ("Сильная морось", "🌧️"),
    61: ("Лёгкий дождь", "🌧️"),
    63: ("Дождь", "🌧️"),
    65: ("Сильный дождь", "🌧️"),
    71: ("Лёгкий снег", "❄️"),
    73: ("Снег", "❄️"),
    75: ("Сильный снег", "❄️"),
    80: ("Лёгкий ливень", "🌧️"),
    81: ("Ливень", "🌧️"),
    82: ("Сильный ливень", "🌧️"),
    95: ("Гроза", "⛈️"),
    96: ("Гроза с градом", "⛈️"),
    99: ("Сильная гроза с градом", "⛈️")
}

async def weather_command(client: Client, message: Message):
    """Обрабатывает команду погода: текущая погода через OpenWeatherMap, прогноз через Open-Meteo."""
    try:
        user_id = message.from_user.id
        chat_id = message.chat.id
        prefix = await get_user_prefix(user_id)  # Асинхронный вызов
        logger.info(f"Обработка команды погода для user_id={user_id}, chat_id={chat_id}, префикс: '{prefix}'")

        # Проверяем наличие API-ключа
        if not OPENWEATHERMAP_API_KEY or OPENWEATHERMAP_API_KEY == "YOUR_API_KEY":
            await message.edit_text("❌ API-ключ OpenWeatherMap не настроен. Проверьте config.py")
            logger.error("API-ключ OpenWeatherMap не настроен в config.py")
            return

        # Парсим аргументы команды
        text = message.text.strip()
        parts = text.split()
        if len(parts) < 2:
            await message.edit_text(f"❌ Укажите город: `{prefix} погода <город> [дата]`")
            return

        args = parts[1:]  # Убираем префикс
        if args[0].lower() != "погода":
            await message.edit_text(f"❌ Неверная команда. Используйте `{prefix} погода <город> [дата]`")
            return

        args = args[1:]  # Убираем "погода"
        if not args:
            await message.edit_text(f"❌ Укажите город: `{prefix} погода <город> [дата]`")
            return

        city = args[0]
        date_str = args[1] if len(args) > 1 else None

        async with aiohttp.ClientSession() as session:
            if not date_str:
                # Текущая погода через OpenWeatherMap
                params = {
                    "q": city,
                    "appid": OPENWEATHERMAP_API_KEY,
                    "units": "metric",
                    "lang": "ru"
                }
                async with session.get(WEATHER_URL, params=params) as resp:
                    if resp.status == 401:
                        await message.edit_text("❌ Неверный или неактивный API-ключ OpenWeatherMap")
                        logger.error(f"Ошибка API для города {city}: Неверный ключ (401)")
                        return
                    if resp.status != 200:
                        await message.edit_text("❌ Город не найден или ошибка API")
                        logger.error(f"Ошибка API для города {city}: {resp.status}")
                        return
                    data = await resp.json()
                    if data.get("cod") != 200:
                        await message.edit_text("❌ Город не найден")
                        logger.error(f"Город {city} не найден: {data.get('message')}")
                        return

                # Форматируем текущую погоду
                weather = data["weather"][0]
                main = data["main"]
                wind = data["wind"]
                response = (
                    f"🌤️ **Погода в {city}**:\n"
                    f"Температура: {main['temp']:.1f}°C\n"
                    f"Ощущается: {main['feels_like']:.1f}°C\n"
                    f"Описание: {weather['description'].capitalize()}\n"
                    f"Влажность: {main['humidity']}%\n"
                    f"Ветер: {wind['speed']} м/с"
                )
                await message.edit_text(response)
                logger.info(f"Текущая погода для {city} отправлена для user_id={user_id}")

            else:
                # Прогноз на дату через Open-Meteo
                if not re.match(r"^\d{2}\.\d{2}\.\d{4}$", date_str):
                    await message.edit_text("❌ Неверный формат даты. Используйте DD.MM.YYYY")
                    return

                try:
                    target_date = datetime.strptime(date_str, "%d.%m.%Y")
                except ValueError:
                    await message.edit_text("❌ Неверная дата")
                    return

                now = datetime.utcnow()
                max_date = now + timedelta(days=16)  # Open-Meteo до 16 дней
                if target_date.date() < now.date() or target_date.date() > max_date.date():
                    await message.edit_text("❌ Прогноз доступен только на сегодня и до 16 дней вперёд")
                    return

                # Шаг 1: Получаем координаты города через OpenWeatherMap Geocoding API
                params = {
                    "q": city,
                    "limit": 1,
                    "appid": OPENWEATHERMAP_API_KEY
                }
                async with session.get(GEOCODING_URL, params=params) as resp:
                    if resp.status == 401:
                        await message.edit_text("❌ Неверный или неактивный API-ключ OpenWeatherMap")
                        logger.error(f"Ошибка Geocoding API для города {city}: Неверный ключ (401)")
                        return
                    if resp.status != 200 or not await resp.json():
                        await message.edit_text("❌ Город не найден")
                        logger.error(f"Ошибка Geocoding API для города {city}: {resp.status}")
                        return
                    geo_data = await resp.json()
                    lat, lon = geo_data[0]["lat"], geo_data[0]["lon"]

                # Шаг 2: Запрашиваем прогноз через Open-Meteo
                params = {
                    "latitude": lat,
                    "longitude": lon,
                    "hourly": "temperature_2m,weather_code,wind_speed_10m",
                    "timezone": "auto"
                }
                async with session.get(OPEN_METEO_URL, params=params) as resp:
                    if resp.status != 200:
                        await message.edit_text("❌ Ошибка при получении прогноза")
                        logger.error(f"Ошибка Open-Meteo API для {city}: {resp.status}")
                        return
                    data = await resp.json()

                # Фильтруем почасовой прогноз
                hourly = data.get("hourly", {})
                times = hourly.get("time", [])
                temps = hourly.get("temperature_2m", [])
                codes = hourly.get("weather_code", [])
                winds = hourly.get("wind_speed_10m", [])

                target_date_str = target_date.strftime("%Y-%m-%d")
                forecast = [
                    {"time": t, "temp": temp, "code": code, "wind": wind}
                    for t, temp, code, wind in zip(times, temps, codes, winds)
                    if t.startswith(target_date_str)
                ]

                if not forecast:
                    await message.edit_text("❌ Прогноз недоступен для этой даты")
                    logger.info(f"Прогноз для {city} на {date_str} не найден")
                    return

                # Группируем по времени суток
                night = [h for h in forecast if 0 <= datetime.strptime(h["time"], "%Y-%m-%dT%H:%M").hour < 6]
                morning = [h for h in forecast if 6 <= datetime.strptime(h["time"], "%Y-%m-%dT%H:%M").hour < 12]
                day = [h for h in forecast if 12 <= datetime.strptime(h["time"], "%Y-%m-%dT%H:%M").hour < 18]
                evening = [h for h in forecast if 18 <= datetime.strptime(h["time"], "%Y-%m-%dT%H:%M").hour < 24]

                # Находим мин и макс температуру
                min_temp = min(h["temp"] for h in forecast)
                max_temp = max(h["temp"] for h in forecast)

                # Форматируем прогноз
                response = f"🌤️ **Погода в {city} на {date_str}**\n"
                response += f"Мин: {min_temp:.1f}°C, Макс: {max_temp:.1f}°C\n\n"

                def format_period(period, period_name, emoji):
                    if not period:
                        return ""
                    result = f"{emoji} **{period_name}**:\n"
                    for hour in period:
                        time = datetime.strptime(hour["time"], "%Y-%m-%dT%H:%M").strftime("%H:%M")
                        desc, icon = WEATHER_CODE_MAP.get(hour["code"], ("Неизвестно", "❓"))
                        result += (
                            f"{time}: {hour['temp']:.1f}°C {icon} {desc:<20} Ветер: {hour['wind']:.1f} м/с\n"
                        )
                    return result + "\n"

                response += format_period(night, "Ночь", "🌙")
                response += format_period(morning, "Утро", "🌅")
                response += format_period(day, "День", "☀️")
                response += format_period(evening, "Вечер", "🌄")

                await message.edit_text(response.strip())
                logger.info(f"Почасовой прогноз для {city} на {date_str} отправлен для user_id={user_id}")

    except Exception as e:
        logger.error(f"Ошибка в weather_command для user_id={user_id}: {e}")
        try:
            await message.edit_text("⚠️ Ошибка при получении данных о погоде")
        except Exception as edit_e:
            logger.error(f"Не удалось отредактировать сообщение: {edit_e}")

def register(app: Client):
    """Регистрирует обработчик команды погода."""
    app.on_message(template_filter("погода", ignore_case=True) & filters.me)(weather_command)