from pyrogram import Client, filters
from pyrogram.types import Message
import asyncio

async def delete_my_messages(client: Client, message: Message):
    try:
        if len(message.command) < 2:
            await message.edit("❌ Укажите количество сообщений для удаления: `.дд 5`")
            return

        count = int(message.text.split()[1])
        if count <= 0:
            await message.edit("❌ Число должно быть больше 0")
            return

        await message.delete()
        
        async for msg in client.search_messages(
            chat_id=message.chat.id,
            from_user="me",
            limit=count
        ):
            try:
                await msg.delete()
                await asyncio.sleep(0.2)
            except Exception as e:
                print(f"Ошибка при удалении: {e}")

    except ValueError:
        await message.edit("❌ Укажите корректное число")
    except Exception as e:
        await message.edit(f"⚠️ Ошибка: {str(e)}")

async def edit_and_delete_messages(client: Client, message: Message):
    try:
        if len(message.command) < 2:
            await message.edit("❌ Укажите количество сообщений: `.дд- 5`")
            return

        count = int(message.text.split()[1])
        if count <= 0:
            await message.edit("❌ Число должно быть больше 0")
            return

        await message.delete()
        
        async for msg in client.search_messages(
            chat_id=message.chat.id,
            from_user="me",
            limit=count
        ):
            try:
                await msg.edit("🫥🫥🫥")
                await asyncio.sleep(0.3)
                await msg.delete()
                await asyncio.sleep(0.2)
            except Exception as e:
                print(f"Ошибка при обработке сообщения: {e}")

    except ValueError:
        await message.edit("❌ Укажите корректное число")
    except Exception as e:
        await message.edit(f"⚠️ Ошибка: {str(e)}")

def register(app: Client):
    app.on_message(filters.command("дд", prefixes=".") & filters.me)(delete_my_messages)
    app.on_message(filters.command("дд-", prefixes=".") & filters.me)(edit_and_delete_messages)