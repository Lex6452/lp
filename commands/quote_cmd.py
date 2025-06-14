import logging
import os
import textwrap
from PIL import Image, ImageDraw, ImageFont
from pyrogram import Client, filters
from pyrogram.types import Message
from utils.filters import template_filter

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Константы
DEFAULT_FONT = "resources/fonts/DejaVuSans.ttf"
EMOJI_FONT = "resources/fonts/NotoColorEmoji.ttf"
TEMPLATE_PATH = "resources/quote_template.jpg"
MAX_TEXT_LENGTH = 500
MAX_USERNAME_LENGTH = 30
AVATAR_SIZE = (150, 150)
AVATAR_POSITION = (50, 50)
TEXT_AREA_LEFT = AVATAR_POSITION[0] + AVATAR_SIZE[0] + 30
TEXT_COLOR = (255, 255, 255)

async def create_circle_mask(size: tuple) -> Image.Image:
    """Создаёт круглую маску для аватарки."""
    mask = Image.new('L', size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, *size), fill=255)
    return mask

async def load_font(font_path: str, font_size: int) -> ImageFont.FreeTypeFont:
    """Загружает шрифт с обработкой ошибок и логированием."""
    try:
        return ImageFont.truetype(font_path, font_size)
    except Exception as e:
        logger.error(f"Ошибка загрузки шрифта {font_path}: {e}")
        return ImageFont.load_default()

async def draw_text_with_emoji(draw: ImageDraw.Draw, position: tuple, text: str, 
                             font: ImageFont.FreeTypeFont, emoji_font: ImageFont.FreeTypeFont, 
                             fill: tuple) -> float:
    """
    Рисует текст с поддержкой эмодзи и возвращает ширину текста.
    """
    x, y = position
    total_width = 0
    logger.info(f"Отрисовка текста: '{text}' на ({x}, {y})")
    
    for char in text:
        try:
            current_font = emoji_font if ord(char) >= 0x1F000 else font
            bbox = current_font.getbbox(char)
            char_width = bbox[2] - bbox[0]
            draw.text((x, y), char, fill=fill, font=current_font)
            x += char_width
            total_width += char_width
        except Exception as e:
            logger.warning(f"Ошибка с символом '{char}': {e}, пропускаю")
            x += font.size // 2
            total_width += font.size // 2
    
    return total_width

async def calculate_font_size(text: str, max_width: int) -> int:
    """Вычисляет оптимальный размер шрифта на основе длины текста."""
    text_length = len(text)
    if text_length < 50:
        return 36
    elif text_length < 100:
        return 30
    elif text_length < 200:
        return 24
    elif text_length < 300:
        return 20
    else:
        return 18

async def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list:
    """Переносит текст по словам с учётом реальной ширины."""
    lines = []
    current_line = []
    for word in text.split():
        test_line = ' '.join(current_line + [word])
        bbox = font.getbbox(test_line)
        test_width = bbox[2] - bbox[0]
        if test_width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    if current_line:
        lines.append(' '.join(current_line))
    return lines[:10]

async def create_quote(client: Client, user_id: int, username: str, text: str, output_path: str) -> bool:
    """Создает изображение цитаты с учетом всех требований."""
    avatar_path = f"quotes/temp_avatar_{user_id}.jpg"
    
    try:
        # Загрузка и подготовка шаблона
        try:
            canvas = Image.open(TEMPLATE_PATH).convert('RGB')
            canvas_width, canvas_height = canvas.size
        except Exception as e:
            logger.error(f"Ошибка загрузки шаблона: {e}")
            canvas = Image.new('RGB', (800, 500), (40, 40, 40))
            canvas_width, canvas_height = 800, 500
        
        draw = ImageDraw.Draw(canvas)
        
        # Загрузка и обработка аватарки
        avatar = Image.new('RGB', AVATAR_SIZE, (200, 200, 200))  # Заглушка
        try:
            async for photo in client.get_chat_photos(user_id, limit=1):
                await client.download_media(photo.file_id, avatar_path)
                avatar = Image.open(avatar_path).convert('RGB').resize(AVATAR_SIZE, Image.Resampling.LANCZOS)
                break
        except Exception as e:
            logger.warning(f"Ошибка загрузки аватарки: {e}")
        
        # Создание круглой аватарки
        mask = await create_circle_mask(AVATAR_SIZE)
        if mask:
            avatar.putalpha(mask)
            canvas.paste(avatar, AVATAR_POSITION, avatar)
        
        # Отрисовка имени пользователя
        username = username[:MAX_USERNAME_LENGTH]
        name_font = await load_font(DEFAULT_FONT, 24)
        emoji_font = await load_font(EMOJI_FONT, 24)
        name_width = await draw_text_with_emoji(draw, (0, 0), username, name_font, emoji_font, (0, 0, 0))
        name_x = AVATAR_POSITION[0] + (AVATAR_SIZE[0] - name_width) // 2
        name_y = AVATAR_POSITION[1] + AVATAR_SIZE[1] + 20
        await draw_text_with_emoji(draw, (name_x, name_y), username, name_font, emoji_font, TEXT_COLOR)
        
        # Подготовка текста цитаты
        text = text[:MAX_TEXT_LENGTH]
        max_text_width = canvas_width - TEXT_AREA_LEFT - 50
        
        # Динамический размер шрифта
        font_size = await calculate_font_size(text, max_text_width)
        text_font = await load_font(DEFAULT_FONT, font_size)
        emoji_text_font = await load_font(EMOJI_FONT, font_size)
        
        # Перенос текста
        lines = await wrap_text(text, text_font, max_text_width)
        
        # Расчет вертикального центрирования
        line_height = int(font_size * 1.2)
        total_text_height = len(lines) * line_height
        text_y = (canvas_height - total_text_height) // 2
        
        # Отрисовка текста
        for line in lines:
            await draw_text_with_emoji(draw, (TEXT_AREA_LEFT, text_y), line, text_font, emoji_text_font, TEXT_COLOR)
            text_y += line_height
        
        # Сохранение результата
        canvas.save(output_path, "JPEG", quality=95)
        logger.info(f"Цитата сохранена: {output_path}")
        return True
    
    except Exception as e:
        logger.error(f"Ошибка при создании цитаты: {e}")
        return False
    finally:
        if os.path.exists(avatar_path):
            os.remove(avatar_path)

async def quote_cmd(client: Client, message: Message):
    """Обработчик команды цитаты."""
    if not message.reply_to_message or not message.reply_to_message.text:
        await message.edit("❌ Ответьте на текстовое сообщение!")
        return
    
    user = message.reply_to_message.from_user
    if not user:
        await message.edit("❌ Не удалось получить пользователя!")
        return
    
    user_id = user.id
    username = f"{user.first_name or 'Аноним'} {user.last_name or ''}".strip()
    text = message.reply_to_message.text
    
    os.makedirs("quotes", exist_ok=True)
    output_path = f"quotes/quote_{message.id}.jpg"
    
    try:
        if await create_quote(client, user_id, username, text, output_path):
            await message.delete()
            await client.send_photo(message.chat.id, output_path)
            logger.info(f"Цитата отправлена для пользователя {message.from_user.id}")
        else:
            await message.edit("❌ Ошибка создания цитаты!")
    except Exception as e:
        await message.edit(f"⚠️ Ошибка: {str(e)}")
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)

def register(app: Client):
    app.on_message(template_filter("цитата") & filters.me)(quote_cmd)