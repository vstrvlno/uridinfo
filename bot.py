import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from aiohttp import web
from dotenv import load_dotenv

from unified_api import get_company_data  # импортируем функцию из unified_api

# --- Настройка логов и окружения ---
logging.basicConfig(level=logging.INFO)
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
EGOV_API_KEY = os.getenv("EGOV_API_KEY")
PORT = int(os.getenv("PORT", 8080))

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher()


# --- Команда /start ---
@dp.message(Command("start"))
async def start_cmd(message: Message):
    await message.answer(
        "👋 Привет! Я помогу найти информацию о компании по данным из открытых источников РК.\n\n"
        "Просто отправь мне название компании или БИН.\n\n"
        "Пример: <b>КазОйлГрупп-2009</b> или <b>090340013951</b>"
    )


# --- Обработка текстовых запросов ---
@dp.message()
async def handle_search(message: Message):
    query = message.text.strip()
    if not query:
        await message.answer("❗ Введи название компании или БИН.")
        return

    await message.answer("🔍 Ищу данные, подожди немного...")

    try:
        data = await get_company_data(query)
        if not data:
            await message.answer("❌ Компания не найдена. Попробуй уточнить название.")
            return

        text = (
            f"<b>🏢 Название:</b> {data['name']}\n"
            f"<b>📇 БИН:</b> {data['bin']}\n"
            f"<b>📍 Адрес:</b> {data['address']}\n"
            f"<b>📅 Регистрация:</b> {data['registration_date']}\n"
            f"<b>💼 Вид деятельности:</b> {data['oked_name']}\n"
            f"<b>👤 Руководитель:</b> {data['director']}"
        )
        await message.answer(text)
    except Exception as e:
        logging.error(f"Ошибка при поиске: {e}")
        await message.answer("⚠️ Произошла ошибка при получении данных. Попробуй позже.")


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
