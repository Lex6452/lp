import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.handlers import RawUpdateHandler
from pyrogram.types import Message
from config import api_id, api_hash, db_config
from db.db_utils import init_db
from commands.type_cmd import register as register_type
from commands.hack_cmd import register as register_hack
from commands.speedtest_cmd import register as register_speedtest
from commands.template_cmd import register as register_template
from commands.delete_cmd import register as register_delete
from commands.voice_cmd import register as register_voice
from commands.speed_server_cmd import register as register_speed_server
from commands.animation_cmd import register as register_animation
from commands.help_cmd import register as register_help
from commands.video_note_cmd import register as register_video_note
from commands.megapush_cmd import register as register_megapush
from commands.choose_cmd import register as register_choose
from commands.fake_activity_cmd import register as register_fake_activity
from commands.online_cmd import register as register_online
from commands.prefix_cmd import register as register_prefix
from commands.profile_cmd import register as register_profile
from commands.alias_cmd import register as register_alias
from commands.demotivator_cmd import register as register_demotivator
from commands.quote_cmd import register as register_quote
from commands.screenshot_cmd import register as register_screenshot
from commands.redach_cmd import register as register_redach
from commands.udalyalka_cmd import register as register_udalyalka
from commands.spam_cmd import register as register_spam
from commands.interval_cmd import register as register_interval
from commands.ping_cmd import register as register_ping
from commands.advice_cmd import register as register_advice
from commands.trap_cmd import register as register_trap
from commands.weather_cmd import register as register_weather
from commands.space_cmd import register as register_space
from commands.cat_cmd import register as register_cat
from commands.ip_cmd import register as register_ip
from commands.whois_cmd import register as register_whois
from commands.conv_cmd import register as register_conv
from commands.id_cmd import register as register_id

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log')
    ]
)
logger = logging.getLogger(__name__)

app = Client("my_account", api_id=api_id, api_hash=api_hash)

# Фильтр для игнорирования некорректных команд
def safe_command_filter(_: Client, __: any, message: Message):
    if message.text is None or not message.text.strip():
        return False
    # Игнорируем сообщения, начинающиеся с некорректных символов
    invalid_prefixes = ['.*', '.+', '.?', '.{', '.(', '.[']
    return (
        message.text.startswith('.') and
        not any(message.text.startswith(prefix) for prefix in invalid_prefixes)
    )

def register_all_commands(app):
    register_type(app)
    register_hack(app)
    register_speedtest(app)
    register_template(app)
    register_delete(app)
    register_voice(app)
    register_speed_server(app)
    register_animation(app)
    register_help(app)
    register_video_note(app)
    register_megapush(app)
    register_choose(app)
    register_fake_activity(app)
    register_online(app)
    register_prefix(app)
    register_profile(app)
    register_alias(app)
    register_demotivator(app)
    register_quote(app)
    register_screenshot(app)
    register_redach(app)
    register_udalyalka(app)
    register_spam(app)
    register_interval(app)
    register_ping(app)
    register_advice(app)
    register_trap(app)
    register_weather(app)
    register_space(app)
    register_cat(app)
    register_ip(app)
    register_whois(app)
    register_conv(app)
    register_id(app)

async def error_handler(client: Client, update, users: dict, chats: dict):
    """Глобальный обработчик ошибок для логирования."""
    # Игнорируем обновления, не связанные с сообщениями
    if not isinstance(update, Message):
        return True  # Пропускаем обработку

    update_text = getattr(update, 'text', 'Нет текста')
    media_type = getattr(update, 'media', None)
    update_details = {
        'type': type(update).__name__,
        'chat_id': getattr(update, 'chat', {}).get('id', 'Неизвестно'),
        'text': update_text,
        'media': str(media_type) if media_type else 'Нет медиа',
        'from_user': getattr(update, 'from_user', {}).get('id', 'Неизвестно'),
        'users': list(users.keys()) if users else [],
        'chats': list(chats.keys()) if chats else []
    }
    logger.error(f"Ошибка при обработке обновления: {type(update).__name__}, детали: {update_details}")
    return True  # Продолжить обработку других фильтров

if __name__ == "__main__":
    init_db()
    register_all_commands(app)
    # Регистрируем обработчик ошибок
    app.add_handler(RawUpdateHandler(error_handler), group=-1)
    # Добавляем фильтр для всех сообщений
    app.on_message(filters.create(safe_command_filter))
    logger.info("Бот запускается...")
    app.run()