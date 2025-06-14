import logging
import re
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from db.db_utils import get_edit_text, get_delete_cmd
from utils.filters import delete_cmd_trigger_filter

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def handle_delete_commands(client: Client, message: Message):
    try:
        cmd_text = message.text.strip().lower()  # Приводим к нижнему регистру
        logger.info(f"Обработка команды: {cmd_text}")
        
        # Получаем текущую команду удаления и текст редактирования
        delete_cmd = (await get_delete_cmd(message.from_user.id)).lower()  # Приводим к нижнему регистру
        edit_text = await get_edit_text(message.from_user.id)
        logger.info(f"Текущая команда удаления: {delete_cmd}")
        
        # Определяем количество сообщений и тип команды
        count = 1  # По умолчанию
        is_edit = cmd_text.startswith(f"{delete_cmd}-")  # Проверяем, редактировать ли перед удалением
        
        if cmd_text == delete_cmd:
            # Точное совпадение: удаляем 1 сообщение
            pass
        elif re.match(f"^{re.escape(delete_cmd)}\d+$", cmd_text):
            # Формат `<delete_cmd><число>`
            count = int(cmd_text[len(delete_cmd):])
        elif re.match(f"^{re.escape(delete_cmd)}\s+(\d+)$", cmd_text):
            # Формат `<delete_cmd> <число>`
            count = int(re.match(f"^{re.escape(delete_cmd)}\s+(\d+)$", cmd_text).group(1))
        elif cmd_text == f"{delete_cmd}-":
            # Точное совпадение: редактируем и удаляем 1 сообщение
            pass
        elif re.match(f"^{re.escape(delete_cmd)}-\d+$", cmd_text):
            # Формат `<delete_cmd>-<число>`
            count = int(cmd_text[len(delete_cmd)+1:])
        elif re.match(f"^{re.escape(delete_cmd)}-\s+(\d+)$", cmd_text):
            # Формат `<delete_cmd>- <число>`
            count = int(re.match(f"^{re.escape(delete_cmd)}-\s+(\d+)$", cmd_text).group(1))
        else:
            # Показываем пример с оригинальным регистром команды
            original_cmd = await get_delete_cmd(message.from_user.id)
            await message.edit(f"❌ Укажите корректную команду: `{original_cmd} 5`, `{original_cmd}5`, `{original_cmd}`, `{original_cmd}- 5`, `{original_cmd}-5`, `{original_cmd}-`")
            return

        if count <= 0:
            await message.edit(f"❌ Число должно быть больше 0")
            return

        await message.delete()
        
        if count == 1:
            # Обработка 1 сообщения
            async for msg in client.search_messages(
                chat_id=message.chat.id,
                from_user="me",
                limit=1
            ):
                try:
                    if is_edit:
                        await msg.edit(edit_text)
                        await asyncio.sleep(0.3)
                    await msg.delete()
                    logger.info(f"{'Отредактировано и удалено' if is_edit else 'Удалено'} 1 сообщение для user_id={message.from_user.id}")
                except Exception as e:
                    logger.error(f"Ошибка при обработке сообщения {msg.id}: {e}")
        else:
            # Массовое удаление/редактирование
            messages = []
            async for msg in client.search_messages(
                chat_id=message.chat.id,
                from_user="me",
                limit=count
            ):
                messages.append(msg)
            
            if messages:
                if is_edit:
                    # Сначала редактируем все сообщения
                    for msg in messages:
                        try:
                            await client.edit_message_text(
                                chat_id=message.chat.id,
                                message_id=msg.id,
                                text=edit_text
                            )
                            await asyncio.sleep(0.1)
                        except Exception as e:
                            logger.error(f"Ошибка при редактировании сообщения {msg.id}: {e}")
                
                # Затем удаляем все сообщения
                message_ids = [msg.id for msg in messages]
                await client.delete_messages(message.chat.id, message_ids)
                logger.info(f"{'Массово отредактировано и удалено' if is_edit else 'Массово удалено'} {len(messages)} сообщений для user_id={message.from_user.id}")
            else:
                logger.warning(f"Нет сообщений для {'редактирования/удаления' if is_edit else 'удаления'}: user_id={message.from_user.id}")

    except ValueError:
        await message.edit("❌ Укажите корректное число")
    except Exception as e:
        await message.edit(f"⚠️ Ошибка: {str(e)}")
        logger.error(f"Ошибка в handle_delete_commands: {e}")

def register(app: Client):
    app.on_message(filters.create(delete_cmd_trigger_filter))(handle_delete_commands)