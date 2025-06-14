import requests
from pyrogram import Client, filters
from pyrogram.types import Message
from commands.template_cmd import template_filter

async def cat_command(client: Client, message: Message):
    """Отправляет случайное фото котика с TheCatAPI."""
    try:
        response = requests.get("https://api.thecatapi.com/v1/images/search")
        if response.status_code == 200:
            cat_url = response.json()[0]["url"]
            await message.delete()
            await client.send_photo(message.chat.id, cat_url)
        else:
            await message.edit("😿 Не удалось загрузить котика...")
    except Exception as e:
        await message.edit(f"⚠️ Ошибка: {str(e)}")

def register(app: Client):
    app.on_message(template_filter("котик", ignore_case=True) & filters.me)(cat_command)
