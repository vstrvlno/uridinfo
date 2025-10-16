import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from aiohttp import web
from dotenv import load_dotenv

import unified_api  # импортируем наш универсальный парсер

# --- Настройка логов и окружения ---
logging.basicConfig(level=logging.INFO)
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 8080))

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher()


# --- Команды ---
@dp.message(Command("start"))
async def start_cmd(message: Message):
    await message.answer(
        "👋 Привет! Отправь мне название компании, и я покажу информацию из открытых источников РК.\n\n"
        "Пример: <b>КазОйлГрупп-2009</b>"
    )


@dp.message()
async def handle_search(message: Message):
    query = message.text.strip()
    await message.answer("🔍 Ищу данные, подожди немного...")

    result = await unified_api.search_company(query)
    if result:
        await message.answer(result)
    else:
        await message.answer("❌ Компания не найдена. Попробуй уточнить название.")


# --- Для Render (Webhook сервер) ---
async def handle_request(request):
    return web.Response(text="Bot is running!")


async def on_startup():
    app = web.Application()
    app.router.add_get("/", handle_request)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logging.info(f"✅ Webhook сервер запущен на порту {PORT}")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(on_startup())
