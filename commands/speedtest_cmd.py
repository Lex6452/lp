from pyrogram import Client, filters
from pyrogram.types import Message
import asyncio
import subprocess
import json
from utils.speedtest_utils import format_speedtest_results

async def speedtest_cmd(client: Client, message: Message):
    try:
        msg = await message.edit("⏳ Запуск теста скорости...")

        async def run_speedtest():
            try:
                result = await asyncio.to_thread(
                    subprocess.run,
                    ["speedtest", "--format=json"],
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    raise Exception(f"Speedtest error: {result.stderr}")
                return json.loads(result.stdout)
            except Exception as e:
                print(f"Speedtest error: {e}")
                return None

        data = await run_speedtest()
        
        if not data:
            await msg.edit("❌ Ошибка при выполнении теста скорости")
            return

        result_text = format_speedtest_results(data)
        await msg.edit(result_text)

    except Exception as e:
        await message.edit(f"⚠️ Ошибка: {str(e)}")
        print(f"Speedtest command error: {e}")

def register(app: Client):
    app.on_message(filters.command("speedtest", prefixes=".") & filters.me)(speedtest_cmd)