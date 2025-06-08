from pyrogram import Client, filters
from pyrogram.types import Message
from db.db_utils import template_exists, save_template, get_template, delete_template, list_templates
from utils.filters import template_filter, simple_cmd_filter

async def save_template_cmd(client: Client, message: Message):
    try:
        if not message.reply_to_message or not message.reply_to_message.text:
            await message.edit("❌ Ответьте на текстовое сообщение!")
            return

        template_name = message.text.split(maxsplit=1)[1].strip()
        user_id = message.from_user.id
        template_text = message.reply_to_message.text

        if await template_exists(user_id, template_name):
            await message.edit(f"❌ Шаблон '{template_name}' уже существует!")
            return

        if await save_template(user_id, template_name, template_text):
            await message.edit(f"✅ Шаблон '{template_name}' сохранен!")
        else:
            await message.edit("❌ Ошибка сохранения!")
    except Exception as e:
        await message.edit(f"⚠️ Ошибка: {str(e)}")

async def get_template_cmd(client: Client, message: Message):
    try:
        template_name = message.text.split(maxsplit=1)[1].strip()
        user_id = message.from_user.id
        template_text = await get_template(user_id, template_name)

        if template_text:
            await message.edit(template_text)
        else:
            await message.edit(f"❌ Шаблон '{template_name}' не найден!")
    except Exception as e:
        await message.edit(f"⚠️ Ошибка: {str(e)}")

async def delete_template_cmd(client: Client, message: Message):
    try:
        template_name = message.text.split(maxsplit=1)[1].strip()
        user_id = message.from_user.id

        if await delete_template(user_id, template_name):
            await message.edit(f"🗑️ Шаблон '{template_name}' удален!")
        else:
            await message.edit(f"❌ Шаблон '{template_name}' не найден!")
    except Exception as e:
        await message.edit(f"⚠️ Ошибка: {str(e)}")

async def list_templates_cmd(client: Client, message: Message):
    try:
        user_id = message.from_user.id
        templates = await list_templates(user_id)

        if not templates:
            await message.edit("📂 У вас нет шаблонов!")
        else:
            templates_list = "\n".join(f"{i+1}. {name}" for i, name in enumerate(templates))
            await message.edit(f"📂 Ваши шаблоны:\n\n{templates_list}\n\nВсего: {len(templates)}")
    except Exception as e:
        await message.edit(f"⚠️ Ошибка: {str(e)}")

def register(app: Client):
    app.on_message(template_filter("+шаб") & filters.me)(save_template_cmd)
    app.on_message(template_filter("шаб") & filters.me)(get_template_cmd)
    app.on_message(template_filter("-шаб") & filters.me)(delete_template_cmd)
    app.on_message(simple_cmd_filter("шабы") & filters.me)(list_templates_cmd)