from pyrogram import Client, filters
from pyrogram.types import Message
import random

# Фильтр для команды .выбери
def choose_filter(_: Client, __, message: Message):
    return (
        message.text is not None and
        message.text.startswith('.выбери') and
        len(message.text.split()) > 1 and
        message.from_user and
        message.from_user.is_self
    )

async def choose_cmd(client: Client, message: Message):
    """Выбирает случайный вариант из указанных, разделённых словом 'или'."""
    try:
        # Извлекаем текст после .выбери
        text = message.text[7:].strip()  # Убираем '.выбери' и пробелы
        if not text:
            await message.edit("❌ Укажите варианты, разделённые словом 'или'. Пример: `.выбери чай или кофе`")
            return

        # Разделяем текст по слову 'или' (игнорируем регистр)
        variants = [v.strip() for v in text.split(' или ') if v.strip()]
        if len(variants) < 2:
            await message.edit("❌ Укажите хотя бы два варианта, разделённых словом 'или'. Пример: `.выбери чай или кофе`")
            return

        # Выбираем случайный вариант
        chosen = random.choice(variants)
        await message.edit(f"🎲 Выбран вариант: **{chosen}**")

    except Exception as e:
        await message.edit(f"⚠️ Ошибка: {str(e)}")

def register(app: Client):
    """Регистрирует обработчик команды .выбери."""
    app.on_message(filters.create(choose_filter))(choose_cmd)