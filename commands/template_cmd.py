from pyrogram import Client, filters
from pyrogram.types import Message
from db.db_utils import template_exists, save_template, get_template, delete_template, list_templates, list_categories
from utils.filters import template_filter, simple_cmd_filter
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def save_template_cmd(client: Client, message: Message):
    try:
        if not message.reply_to_message or not message.reply_to_message.text:
            await message.edit("❌ Ответьте на текстовое сообщение!")
            return

        parts = message.text.split(maxsplit=2)
        if len(parts) < 3:
            await message.edit("❌ Укажите имя шаблона, например: <префикс> +шаб мой_шаблон")
            return
        template_info = parts[2].strip().split("|", 1)
        template_name = template_info[0].strip()
        category = "без категории" if len(template_info) < 2 else template_info[1].strip()
        user_id = message.from_user.id
        template_text = message.reply_to_message.text

        if not template_name:
            await message.edit("❌ Имя шаблона не может быть пустым!")
            return

        if await template_exists(user_id, template_name):
            await message.edit(f"❌ Шаблон '{template_name}' уже существует!")
            return

        if await save_template(user_id, template_name, template_text, category):
            await message.edit(f"✅ Шаблон '{template_name}' сохранен в категории '{category}'!")
        else:
            await message.edit("❌ Ошибка сохранения!")
    except Exception as e:
        await message.edit(f"⚠️ Ошибка: {str(e)}")
        logger.error(f"Ошибка при сохранении шаблона: {e}")

async def get_template_cmd(client: Client, message: Message):
    try:
        parts = message.text.split(maxsplit=2)
        if len(parts) < 3:
            await message.edit("❌ Укажите имя шаблона, например: <префикс> шаб мой_шаблон")
            return
        template_name = parts[2].strip()
        user_id = message.from_user.id
        result = await get_template(user_id, template_name)

        if result:
            template_text, _ = result  # Игнорируем категорию
            await message.edit(template_text)
        else:
            await message.edit(f"❌ Шаблон '{template_name}' не найден!")
    except Exception as e:
        await message.edit(f"⚠️ Ошибка: {str(e)}")
        logger.error(f"Ошибка при получении шаблона: {e}")

async def delete_template_cmd(client: Client, message: Message):
    try:
        parts = message.text.split(maxsplit=2)
        if len(parts) < 3:
            await message.edit("❌ Укажите имя шаблона, например: <префикс> -шаб мой_шаблон")
            return
        template_name = parts[2].strip()
        user_id = message.from_user.id

        if await delete_template(user_id, template_name):
            await message.edit(f"🗑️ Шаблон '{template_name}' удален!")
        else:
            await message.edit(f"❌ Шаблон '{template_name}' не найден!")
    except Exception as e:
        await message.edit(f"⚠️ Ошибка: {str(e)}")
        logger.error(f"Ошибка при удалении шаблона: {e}")

async def list_templates_cmd(client: Client, message: Message):
    try:
        user_id = message.from_user.id
        parts = message.text.strip().split(maxsplit=2)  # <префикс> <команда> <аргумент>
        logger.info(f"Обработка команды: {message.text}, parts={parts}, user_id={user_id}")

        # Команда без аргументов: <префикс> шабы
        if len(parts) < 3 or not parts[2].strip():
            categories = await list_categories(user_id)
            if not categories:
                await message.edit("📂 У вас нет категорий и шаблонов!")
            else:
                categories_list = "\n".join(f"- {cat} ({count})" for cat, count in categories)
                await message.edit(f"Категории шаблонов:\n\n{categories_list}")
            return

        # Получаем аргумент
        arg = parts[2].strip()

        # Команда <префикс> шабы все
        if arg.lower() == "все":
            templates = await list_templates(user_id)
            if not templates:
                await message.edit("📂 У вас нет шаблонов!")
            else:
                templates_list = "\n".join(f"- {name} | {category}" for name, category in templates)
                await message.edit(f"Список всех шаблонов:\n\n{templates_list}")
            return

        # Команда <префикс> шабы <категория>
        category = arg
        templates = await list_templates(user_id, category)
        if not templates:
            await message.edit(f"📂 В категории '{category}' нет шаблонов!")
        else:
            templates_list = "\n".join(f"- {name}" for name, _ in templates)
            await message.edit(f"📚 Шаблоны категории '{category}':\n\n{templates_list}")
    except Exception as e:
        await message.edit(f"⚠️ Ошибка: {str(e)}")
        logger.error(f"Ошибка в list_templates_cmd: {e}")

def register(app: Client):
    app.on_message(simple_cmd_filter("шабы", ignore_case=True) & filters.me)(list_templates_cmd)
    app.on_message(template_filter("+шаб", ignore_case=True) & filters.me)(save_template_cmd)
    app.on_message(template_filter("шаб", ignore_case=True) & filters.me)(get_template_cmd)
    app.on_message(template_filter("-шаб", ignore_case=True) & filters.me)(delete_template_cmd)