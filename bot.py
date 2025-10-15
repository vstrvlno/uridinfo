# bot.py
import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiohttp import web

# Импортируем парсеры — эти модули будут в папке parsers/
from parsers.stat_api import search_by_name, get_company_by_bin
from parsers.kgd_api import get_tax_info
from parsers.court_api import get_court_cases
from parsers.zakup_api import get_goszakup_info
from parsers.licenses_api import get_licenses_info
from parsers.utils import format_full_card, is_bin

# Логи
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 8080))

if not BOT_TOKEN:
    logger.error("BOT_TOKEN is not set")
    raise SystemExit("BOT_TOKEN required")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Главное меню (кнопки)
kb_main = ReplyKeyboardMarkup(resize_keyboard=True)
kb_main.add(KeyboardButton("🔎 Поиск по БИН"), KeyboardButton("🔎 По названию"))
kb_back = ReplyKeyboardMarkup(resize_keyboard=True)
kb_back.add(KeyboardButton("🔙 В меню"))

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Привет! Я бот для проверки юридических лиц Казахстана.\n\n"
        "Выбери способ поиска или отправь сразу БИН/название:",
        reply_markup=kb_main
    )

# Обработка выбора меню
@dp.message(F.text == "🔎 По БИН")
async def ask_bin(message: types.Message):
    await message.answer("Отправь БИН (12 цифр) для поиска.", reply_markup=kb_back)

@dp.message(F.text == "🔎 По названию")
async def ask_name(message: types.Message):
    await message.answer("Отправь название компании (или часть названия) — выдаю до 5 совпадений.", reply_markup=kb_back)

@dp.message(F.text == "🔙 В меню")
async def back_menu(message: types.Message):
    await message.answer("Возвращаю в меню:", reply_markup=kb_main)

# Общая обработка входящих текстов
@dp.message(F.text)
async def handle_text(message: types.Message):
    text = message.text.strip()

    # команды-переключатели
    if text.lower() in ("/menu", "меню"):
        await message.answer("Выбери опцию:", reply_markup=kb_main)
        return

    # показываем индикатор
    await message.chat.do("typing")

    # Если выглядит как БИН — поиск по БИН
    if is_bin(text):
        await message.answer("🔎 Ищу по БИН...")
        try:
            basic = await get_company_by_bin(text)
            if not basic:
                await message.answer("⚠️ Компания по такому БИН не найдена.", reply_markup=kb_back)
                return
            await send_full_card(message.chat.id, basic)
        except Exception as e:
            logger.exception("Ошибка поиска по БИН: %s", e)
            await message.answer("⚠️ Ошибка при поиске по БИН. Попробуйте позже.", reply_markup=kb_back)
        return

    # Иначе — поиск по названию
    await message.answer("🔎 Ищу по названию (до 5 результатов)...")
    try:
        results = await search_by_name(text, limit=5)
        if not results:
            await message.answer("Не найдено совпадений.", reply_markup=kb_back)
            return

        kb = InlineKeyboardMarkup(row_width=1)
        for it in results:
            name = it.get("name") or it.get("title") or "(без названия)"
            bin_ = it.get("bin") or it.get("BIN") or ""
            label = f"{name} — {bin_}" if bin_ else name
            cb_data = f"select:{bin_}"
            kb.add(InlineKeyboardButton(text=label, callback_data=cb_data))

        await message.answer("Найдено несколько компаний. Выберите одну:", reply_markup=kb)
    except Exception as e:
        logger.exception("Ошибка поиска по названию: %s", e)
        await message.answer("⚠️ Ошибка при поиске по названию. Попробуйте позже.", reply_markup=kb_back)

# Обработка выбора результата (callback)
@dp.callback_query(lambda c: c.data and c.data.startswith("select:"))
async def on_select(callback: types.CallbackQuery):
    await callback.answer()  # убираем часики у кнопки
    bin_ = callback.data.split(":", 1)[1]
    if not bin_:
        await callback.message.answer("У выбранной записи нет БИН. Попробуйте более точный поиск.", reply_markup=kb_back)
        return

    await callback.message.chat.do("typing")
    try:
        basic = await get_company_by_bin(bin_)
        if not basic:
            await callback.message.answer("Данные по выбранной компании не найдены.", reply_markup=kb_back)
            return
        await send_full_card(callback.message.chat.id, basic)
    except Exception as e:
        logger.exception("Ошибка при загрузке данных компании: %s", e)
        await callback.message.answer("⚠️ Ошибка при загрузке данных компании.", reply_markup=kb_back)

# Сборка полной карточки (запросы к доп. сервисам параллельно)
async def send_full_card(chat_id: int, basic_info: dict):
    bin_ = basic_info.get("bin") or basic_info.get("BIN")
    # Запросы к доп. источникам (если модуль не вернёт данные — вернётся пустая структура)
    tasks = [
        get_tax_info(bin_),
        get_court_cases(bin_),
        get_goszakup_info(bin_),
        get_licenses_info(bin_),
    ]
    try:
        kgd_data, court_data, zakup_data, lic_data = await asyncio.gather(*tasks)
    except Exception as e:
        logger.warning("Ошибка при сборе доп. данных: %s", e)
        kgd_data, court_data, zakup_data, lic_data = {}, [], [], []

    text = format_full_card(basic_info, kgd_data, court_data, zakup_data, lic_data)

    # Ограничение Telegram на длину сообщения — делим при необходимости
    MAX = 3900
    if len(text) <= MAX:
        await bot.send_message(chat_id, text, parse_mode="Markdown", disable_web_page_preview=True)
    else:
        for i in range(0, len(text), MAX):
            await bot.send_message(chat_id, text[i:i+MAX], parse_mode="Markdown", disable_web_page_preview=True)

# Health endpoint для Render (и других хостингов)
async def start_server():
    app = web.Application()
    async def health(request):
        return web.Response(text="OK")
    app.router.add_get("/", health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logger.info("Health server started on port %s", PORT)

async def main():
    await start_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Stopping bot")
