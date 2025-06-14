import logging
import os
from PIL import Image, ImageDraw, ImageFont
from pyrogram import Client, filters
from pyrogram.types import Message
from db.db_utils import get_user_prefix
from utils.filters import template_filter

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_demotivator(photo_path: str, text: str, output_path: str):
    """Создаёт демотиватор с подписью."""
    try:
        # Открываем шаблон и фото
        template = Image.open('resources/demotivator_template.jpg')
        mem = Image.open(photo_path).convert('RGBA')

        # Изменяем размер фото
        width, height = 610, 569
        resized_mem = mem.resize((width, height), Image.LANCZOS)

        # Параметры подписи
        strip_width, strip_height = 700, 1300
        text_color = (255, 255, 255)  # Красный цвет

        def find_len(text_len):
            return len(text_len)

        font_width = 60
        if find_len(text) >= 25:
            font_width = 50

        draw = ImageDraw.Draw(template)

        if '\n' in text:
            split_offers = text.split('\n')[:2]  # Ограничиваем до 2 строк
            for i in range(len(split_offers)):
                if i == 1:
                    strip_height += 110
                    font_width -= 20
                font = ImageFont.truetype("resources/fonts/arial.ttf", font_width)
                # Используем textbbox вместо textsize
                bbox = draw.textbbox((0, 0), split_offers[i], font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                position = ((strip_width - text_width) / 2, (strip_height - text_height) / 2)
                draw.text(position, split_offers[i], fill=text_color, font=font)
        else:
            font = ImageFont.truetype("resources/fonts/arial.ttf", font_width)
            # Используем textbbox вместо textsize
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            strip_height = 1330
            position = ((strip_width - text_width) / 2, (strip_height - text_height) / 2)
            draw.text(position, text, fill=text_color, font=font)

        # Накладываем фото на шаблон
        template.paste(resized_mem, (54, 32), resized_mem)
        template.save(output_path, "JPEG")
        logger.info(f"Демотиватор сохранён: {output_path}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при создании демотиватора: {e}")
        return False

async def demotivator_cmd(client: Client, message: Message):
    """Создаёт демотиватор с подписью под фотографией."""
    try:
        # Проверяем наличие подписи
        parts = message.text.split(maxsplit=2)
        if len(parts) < 3:
            await message.edit("❌ Формат: <префикс> дем <подпись>")
            return
        text = parts[2].strip()

        # Проверяем наличие фото
        photo = None
        if message.photo:
            photo = message.photo
        elif message.reply_to_message and message.reply_to_message.photo:
            photo = message.reply_to_message.photo
        else:
            await message.edit("❌ Прикрепите фото или ответьте на сообщение с фото!")
            return

        # Проверяем длину подписи
        if len(text) > 100:
            await message.edit("❌ Подпись не должна превышать 100 символов!")
            return

        # Создаём директорию для сохранения
        save_dir = "demotivators"
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        user_id = message.from_user.id
        temp_photo_path = os.path.join(save_dir, f"temp_{user_id}_{message.id}.jpg")
        output_path = os.path.join(save_dir, f"demotivator_{user_id}_{message.id}.jpg")

        # Скачиваем фото
        await client.download_media(photo, temp_photo_path)

        # Создаём демотиватор
        if await create_demotivator(temp_photo_path, text, output_path):
            await message.delete()
            await client.send_photo(message.chat.id, output_path)
            logger.info(f"Демотиватор отправлен для пользователя {user_id}")
        else:
            await message.edit("❌ Ошибка при создании демотиватора!")

        # Очистка временных файлов
        if os.path.exists(temp_photo_path):
            os.remove(temp_photo_path)
        if os.path.exists(output_path):
            os.remove(output_path)

    except Exception as e:
        logger.error(f"Ошибка при выполнении команды демотиватор: {e}")
        await message.edit(f"⚠️ Ошибка: {str(e)}")
        # Очистка в случае ошибки
        if 'temp_photo_path' in locals() and os.path.exists(temp_photo_path):
            os.remove(temp_photo_path)
        if 'output_path' in locals() and os.path.exists(output_path):
            os.remove(output_path)


def register(app: Client):
    app.on_message(template_filter("дем") & filters.me)(demotivator_cmd)