from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait
import asyncio

async def type_cmd(client: Client, message: Message):
    try:
        if len(message.command) < 2:
            await message.edit("❌ Укажите текст после .type")
            return
            
        orig_text = message.text.split(".type", 1)[1].strip()
        text = orig_text
        tbp = ""
        typing_symbol = "▒"

        while tbp != orig_text:
            try:
                await message.edit(tbp + typing_symbol)
                await asyncio.sleep(0.05)
                tbp += text[0]
                text = text[1:]
                await message.edit(tbp)
                await asyncio.sleep(0.05)
            except FloodWait as e:
                await asyncio.sleep(e.x)
    except Exception as e:
        await message.edit(f"Error: {str(e)}")

def register(app: Client):
    app.on_message(filters.command("type", prefixes=".") & filters.me)(type_cmd)