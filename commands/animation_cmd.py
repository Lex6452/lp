from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait
from db.db_utils import anim_exists, save_animation, delete_animation, get_animation, list_animations
from utils.filters import add_anim_filter, delete_anim_filter, get_anim_filter, list_anims_filter
import asyncio

async def add_animation_cmd(client: Client, message: Message):
    try:
        if not message.reply_to_message or not message.reply_to_message.text:
            await message.edit("❌ Ответьте на сообщение с анимацией!")
            return

        anim_name = message.text.split(maxsplit=1)[1].strip()
        user_id = message.from_user.id
        anim_text = message.reply_to_message.text

        # Разбиваем текст на кадры по разделителю #$
        frames = [frame.strip() for frame in anim_text.split("#$") if frame.strip()]
        
        if len(frames) < 2:
            await message.edit("❌ Анимация должна содержать хотя бы 2 кадра!")
            return

        if await anim_exists(user_id, anim_name):
            await message.edit(f"❌ Анимация '{anim_name}' уже существует!")
            return

        if await save_animation(user_id, anim_name, frames):
            await message.edit(f"✅ Анимация '{anim_name}' сохранена ({len(frames)} кадров)!")
        else:
            await message.edit("❌ Ошибка сохранения!")
    except Exception as e:
        await message.edit(f"⚠️ Ошибка: {str(e)}")

async def delete_animation_cmd(client: Client, message: Message):
    try:
        anim_name = message.text.split(maxsplit=1)[1].strip()
        user_id = message.from_user.id

        if await delete_animation(user_id, anim_name):
            await message.edit(f"🗑️ Анимация '{anim_name}' удалена!")
        else:
            await message.edit(f"❌ Анимация '{anim_name}' не найдена!")
    except Exception as e:
        await message.edit(f"⚠️ Ошибка: {str(e)}")

async def list_animations_cmd(client: Client, message: Message):
    try:
        user_id = message.from_user.id
        animations = await list_animations(user_id)

        if not animations:
            await message.edit("📂 У вас нет сохранённых анимаций!")
        else:
            anims_list = "\n".join(f"{i+1}. {name}" for i, name in enumerate(animations))
            await message.edit(f"📂 Ваши анимации:\n\n{anims_list}\n\nВсего: {len(animations)}")
    except Exception as e:
        await message.edit(f"⚠️ Ошибка: {str(e)}")

async def get_animation_cmd(client: Client, message: Message):
    try:
        anim_name = message.text.split(maxsplit=1)[1].strip()
        user_id = message.from_user.id
        frames = await get_animation(user_id, anim_name)

        if not frames:
            await message.edit(f"❌ Анимация '{anim_name}' не найдена!")
            return

        msg = await message.edit(frames[0])
        
        for frame in frames[1:]:
            try:
                await asyncio.sleep(1)  # Задержка между кадрами
                await msg.edit(frame)
            except FloodWait as e:
                await asyncio.sleep(e.x)
            except Exception:
                break  # Прерываем анимацию при ошибке

    except Exception as e:
        await message.edit(f"⚠️ Ошибка: {str(e)}")

def register(app: Client):
    app.on_message(filters.create(add_anim_filter))(add_animation_cmd)
    app.on_message(filters.create(delete_anim_filter))(delete_animation_cmd)
    app.on_message(filters.create(list_anims_filter))(list_animations_cmd)
    app.on_message(filters.create(get_anim_filter))(get_animation_cmd)
