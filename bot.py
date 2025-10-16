import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from aiohttp import web

from parsers.unified_api import search_company, format_result  # ✅ импорт нового универсального парсера

# --- Настройки логирования ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 8080))

if not BOT_TOKEN:
    raise SystemExit("❌ BOT_TOKEN не установлен в переменных окружения")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- Главное меню ---
kb_main = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔎 Поиск по БИН")],
        [KeyboardButton(text="🔎 По названию")]
    ],
    resize_keyboard=True
)

kb_back = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="🔙 В меню")]],
    resize_keyboard=True
)

# --- Команда /start ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Привет! Я бот для проверки юридических лиц Казахстана.\n\n"
        "Можешь ввести *БИН* или *название компании*, а я покажу сводку:",
        reply_markup=kb_main,
        parse_mode="Markdown"
    )

# --- Обработка кнопок ---
@dp.message(F.text == "🔎 Поиск по БИН")
async def ask_bin(message: types.Message):
    await message.answer("📨 Отправь БИН (12 цифр):", reply_markup=kb_back)

@dp.message(F.text == "🔎 По названию")
async def ask_name(message: types.Message):
    await message.answer("📝 Отправь название компании:", reply_markup=kb_back)

@dp.message(F.text == "🔙 В меню")
async def back_to_menu(message: types.Message):
    await message.answer("Главное меню:", reply_markup=kb_main)

# --- Проверка, что строка похожа на БИН ---
def is_bin(text: str) -> bool:
    return text.isdigit() and len(text) == 12

# --- Основная логика поиска ---
@dp.message(F.text)
async def handle_search(message: types.Message):
    query = message.text.strip()
    if not query:
        await message.answer("⚠️ Введи БИН или название компании.")
        return

    await message.answer("🔎 Ищу данные, пожалуйста подожди...")

    try:
        data = await search_company(query)
        if not data:
            await message.answer("❌ Ничего не найдено.", reply_markup=kb_back)
            return

        text = format_result(data)
        if not text.strip():
            await message.answer("❌ Ничего не найдено.", reply_markup=kb_back)
            return

        # Telegram ограничивает сообщение до 4096 символов, разобьём длинные тексты
        for i in range(0, len(text), 3900):
            await message.answer(text[i:i+3900], parse_mode="Markdown", disable_web_page_preview=True)

    except Exception as e:
        logger.exception(f"Ошибка при поиске: {e}")
        await message.answer("⚠️ Произошла ошибка при запросе данных.", reply_markup=kb_back)

# --- Health-check для Render ---
async def start_server():
    app = web.Application()

    async def health(_):
        return web.Response(text="OK")

    app.router.add_get("/", health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logger.info(f"✅ Health сервер запущен на порту {PORT}")

# --- Основной запуск ---
async def main():
    await start_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("⛔ Бот остановлен.")
