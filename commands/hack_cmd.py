from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait
import asyncio
import random

async def hack_cmd(client: Client, message: Message):
    perc = 0
    while perc < 100:
        try:
            await message.edit(f"👮‍ Взлом пентагона... {perc}%")
            perc += random.randint(1, 3)
            await asyncio.sleep(0.1)
        except FloodWait as e:
            await asyncio.sleep(e.x)
    
    await message.edit("🟢 Пентагон успешно взломан!")
    await asyncio.sleep(3)
    await message.edit("👽 Поиск секретных данных об НЛО...")
    
    perc = 0
    while perc < 100:
        try:
            await message.edit(f"👽 Поиск данных... {perc}%")
            perc += random.randint(1, 5)
            await asyncio.sleep(0.15)
        except FloodWait as e:
            await asyncio.sleep(e.x)
    
    await message.edit("🦖 Найдены данные о динозаврах на земле!")

def register(app: Client):
    app.on_message(filters.command("hack", prefixes=".") & filters.me)(hack_cmd)