# bot.py
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

# --- Импортируем парсеры ---
from parsers.stat_api import search_by_name, get_company_by_bin
from parsers.kgd_api import get_tax_debt
from parsers.court_api import get_court_cases
from parsers.zakup_api import get_goszakup_info
from parsers.licenses_api import get_licenses_info
from parsers.utils import format_full_card, is_bin

# --- Логирование ---
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
        "Выбери способ поиска или отправь сразу БИН/название:",
        reply_markup=kb_main
    )

# --- Обработка кнопок ---
@dp.message(F.text == "🔎 Поиск по БИН")
async def ask_bin(message: types.Message):
    await message.answer("Отправь БИН (12 цифр) для поиска.", reply_markup=kb_back)

@dp.message(F.text == "🔎 По названию")
async def ask_name(message: types.Message):
    await message.answer("Отправь название компании — покажу до 5 совпадений.", reply_markup=kb_back)

@dp.message(F.text == "🔙 В меню")
async def back_to_menu(message: types.Message):
    await message.answer("Возвращаюсь в меню:", reply_markup=kb_main)

# --- Обработка текстовых сообщений ---
@dp.message(F.text)
async def handle_text(message: types.Message):
    text = message.text.strip()

    if text.lower() in ("меню", "/menu"):
        await message.answer("Выбери опцию:", reply_markup=kb_main)
        return

    # Проверка — это БИН или название
    if is_bin(text):
        await message.answer("🔍 Ищу по БИН...")
        try:
            company = await get_company_by_bin(text)
            if not company:
                await message.answer("⚠️ Компания по такому БИН не найдена.", reply_markup=kb_back)
                return
            await send_full_card(message.chat.id, company)
        except Exception as e:
            logger.exception(e)
            await message.answer("⚠️ Ошибка при поиске по БИН.", reply_markup=kb_back)
    else:
        await message.answer("🔍 Ищу по названию (до 5 совпадений)...")
        try:
            results = await search_by_name(text, limit=5)
            if not results:
                await message.answer("❌ Ничего не найдено.", reply_markup=kb_back)
                return

            kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=f"{r.get('name', 'Без названия')} — {r.get('bin', '')}",
                            callback_data=f"select:{r.get('bin', '')}"
                        )
                    ]
                    for r in results
                ]
            )
            await message.answer("Выбери компанию:", reply_markup=kb)
        except Exception as e:
            logger.exception(e)
            await message.answer("⚠️ Ошибка при поиске по названию.", reply_markup=kb_back)

# --- Обработка выбора компании ---
@dp.callback_query(F.data.startswith("select:"))
async def select_company(callback: types.CallbackQuery):
    await callback.answer()
    bin_ = callback.data.split(":", 1)[1]
    if not bin_:
        await callback.message.answer("❌ У записи нет БИН.")
        return

    await callback.message.answer("📄 Загружаю данные компании...")
    try:
        company = await get_company_by_bin(bin_)
        if not company:
            await callback.message.answer("❌ Данные не найдены.", reply_markup=kb_back)
            return
        await send_full_card(callback.message.chat.id, company)
    except Exception as e:
        logger.exception(e)
        await callback.message.answer("⚠️ Ошибка при загрузке данных компании.", reply_markup=kb_back)

# --- Сборка полной карточки ---
async def send_full_card(chat_id: int, basic_info: dict):
    bin_ = basic_info.get("bin") or basic_info.get("BIN")

    tasks = [
        get_tax_debt(bin_),
        get_court_cases(bin_),
        get_goszakup_info(bin_),
        get_licenses_info(bin_),
    ]

    try:
        kgd, courts, zakup, lic = await asyncio.gather(*tasks)
    except Exception as e:
        logger.warning(f"Ошибка при сборе данных: {e}")
        kgd, courts, zakup, lic = {}, [], [], []

    text = format_full_card(basic_info, kgd, courts, zakup, lic)

    # Разбиваем на части, если сообщение слишком длинное
    MAX_LEN = 3900
    for i in range(0, len(text), MAX_LEN):
        await bot.send_message(chat_id, text[i:i+MAX_LEN], parse_mode="Markdown", disable_web_page_preview=True)

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
    logger.info(f"Health сервер запущен на порту {PORT}")

# --- Основная функция ---
async def main():
    await start_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен.")
