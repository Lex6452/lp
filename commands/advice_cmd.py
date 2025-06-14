import logging
import os
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from pyrogram import Client, filters
from pyrogram.types import Message
from utils.filters import template_filter
from textwrap import wrap

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Путь к шрифту и изображениям
FONT_PATH = "resources/fonts/arial.ttf"
ADVICE1_PATH = "resources/advice1.jpg"
ADVICE2_PATH = "resources/advice2.jpg"

async def process_advice_image(client: Client, message: Message):
    """Обрабатывает команду эдвайс для создания мема с текстом на изображении."""
    try:
        # Проверяем наличие изображения
        has_photo = message.photo or (message.reply_to_message and message.reply_to_message.photo)
        logger.debug(f"Проверка фото: has_photo={has_photo}, user_id={message.from_user.id}")

        # Получаем текст из подписи или текста сообщения
        top_text = ""
        bottom_text = ""
        if message.caption:
            text_lines = message.caption.split('\n')[1:]  # Пропускаем первую строку с командой
            top_text = text_lines[0].strip() if len(text_lines) > 0 else ""
            bottom_text = text_lines[1].strip() if len(text_lines) > 1 else ""
        elif message.text:
            text_lines = message.text.split('\n')[1:]  # Пропускаем первую строку с командой
            top_text = text_lines[0].strip() if len(text_lines) > 0 else ""
            bottom_text = text_lines[1].strip() if len(text_lines) > 1 else ""
        has_text = bool(top_text or bottom_text)
        logger.debug(f"Тексты: top_text='{top_text}', bottom_text='{bottom_text}', has_text={has_text}")

        # Случай 1: Нет ни картинки, ни текста
        if not has_photo and not has_text:
            if not os.path.exists(ADVICE1_PATH):
                await message.reply(f"❌ Ошибка: файл {ADVICE1_PATH} не найден")
                logger.error(f"Файл {ADVICE1_PATH} не найден")
                return
            with open(ADVICE1_PATH, "rb") as f:
                output = BytesIO(f.read())
                output.name = "advice.jpg"
            await message.delete()
            await client.send_photo(
                chat_id=message.chat.id,
                photo=output,
                reply_to_message_id=message.reply_to_message.id if message.reply_to_message else None
            )
            logger.info(f"Отправлена картинка {ADVICE1_PATH} без текста для user_id={message.from_user.id}")
            return

        # Случай 2: Нет картинки, но есть текст
        if not has_photo and has_text:
            if not os.path.exists(ADVICE2_PATH):
                await message.reply(f"❌ Ошибка: файл {ADVICE2_PATH} не найден")
                logger.error(f"Файл {ADVICE2_PATH} не найден")
                return
            with open(ADVICE2_PATH, "rb") as f:
                output = BytesIO(f.read())
                output.name = "advice.jpg"
            await message.delete()
            await client.send_photo(
                chat_id=message.chat.id,
                photo=output,
                reply_to_message_id=message.reply_to_message.id if message.reply_to_message else None
            )
            logger.info(f"Отправлена картинка {ADVICE2_PATH} без текста для user_id={message.from_user.id}")
            return

        # Случай 3 и 4: Есть картинка (с текстом или без)
        photo = message.photo if message.photo else message.reply_to_message.photo
        photo_file = await client.download_media(photo, in_memory=True)
        img = Image.open(BytesIO(photo_file.getbuffer()))
        logger.debug(f"Загружена пользовательская картинка, размер: {img.size}")

        # Если нет текста, устанавливаем дефолтный (Случай 3)
        if not has_text:
            top_text = "картинка с текстом"
            bottom_text = "(а где текст?)"
            logger.debug(f"Установлены дефолтные тексты: top_text='{top_text}', bottom_text='{bottom_text}'")

        # Создаем объект для рисования
        draw = ImageDraw.Draw(img)
        img_width, img_height = img.size

        # Настройки шрифта (адаптивный размер)
        font_size = int(img_height / 10)
        try:
            if not os.path.exists(FONT_PATH):
                raise FileNotFoundError(f"Шрифт по пути {FONT_PATH} не найден")
            font = ImageFont.truetype(FONT_PATH, font_size)
            logger.debug(f"Шрифт загружен: {FONT_PATH}, размер: {font_size}")
        except Exception as e:
            font = ImageFont.load_default()
            logger.warning(f"Не удалось загрузить шрифт: {e}, используется стандартный")

        # Обработка верхнего текста
        if top_text:
            chars_per_line = int(img_width / (font_size * 0.6))
            wrapped_text = wrap(top_text, width=chars_per_line)
            logger.debug(f"Верхний текст разбит на строки: {wrapped_text}")

            y_position = 10
            for line in wrapped_text:
                text_width = draw.textlength(line, font=font)
                x_position = (img_width - text_width) / 2
                draw.text(
                    (x_position, y_position),
                    line,
                    font=font,
                    fill="white",
                    stroke_width=2,
                    stroke_fill="black"
                )
                y_position += font_size + 5

        # Обработка нижнего текста
        if bottom_text:
            chars_per_line = int(img_width / (font_size * 0.6))
            wrapped_text = wrap(bottom_text, width=chars_per_line)
            logger.debug(f"Нижний текст разбит на строки: {wrapped_text}")

            y_position = img_height - (len(wrapped_text) * (font_size + 5)) - 20
            for line in wrapped_text:
                text_width = draw.textlength(line, font=font)
                x_position = (img_width - text_width) / 2
                draw.text(
                    (x_position, y_position),
                    line,
                    font=font,
                    fill="white",
                    stroke_width=2,
                    stroke_fill="black"
                )
                y_position += font_size + 5

        # Сохраняем результат
        output = BytesIO()
        output.name = "advice.jpg"
        img.save(output, "JPEG")
        output.seek(0)
        logger.debug("Изображение сохранено в буфер")

        # Отправляем результат
        reply_to_id = message.reply_to_message.id if message.reply_to_message else None
        try:
            await message.delete()
        except Exception as e:
            logger.warning(f"Не удалось удалить исходное сообщение: {e}")

        await client.send_photo(
            chat_id=message.chat.id,
            photo=output,
            reply_to_message_id=reply_to_id
        )
        logger.info(f"Мем успешно отправлен для user_id={message.from_user.id}, chat_id={message.chat.id}")

    except Exception as e:
        logger.error(f"Ошибка в process_advice_image для user_id={message.from_user.id}: {e}")
        try:
            await message.reply("⚠️ Ошибка при обработке изображения")
        except Exception as reply_e:
            logger.error(f"Не удалось отправить сообщение об ошибке: {reply_e}")

def register(app: Client):
    """Регистрирует обработчик команды эдвайс."""
    app.on_message(template_filter("эдвайс", ignore_case=True))(process_advice_image)