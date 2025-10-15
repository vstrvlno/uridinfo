# bot.py




@dp.callback_query(lambda c: c.data and c.data.startswith("select:"))
async def on_select_company(callback: types.CallbackQuery):
await callback.message.chat.do('typing')
bin_ = callback.data.split(":", 1)[1]
await callback.answer() # убираем часики на кнопке
try:
basic = await get_company_by_bin(bin_)
if not basic:
await callback.message.answer("⚠️ Данные по выбранной компании не найдены.")
return
await send_full_card(callback.message.chat.id, basic)
except Exception as e:
logger.exception(e)
await callback.message.answer("⚠️ Ошибка при загрузке данных компании.")




async def send_full_card(chat_id: int, basic_info: dict):
# Собираем все данные из разных источников (без кеша)
bin_ = basic_info.get("bin") or basic_info.get("BIN")
name = basic_info.get("name") or basic_info.get("title")


# Запрашиваем сторонние сервисы параллельно
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


# Форматируем карточку
text = format_full_card(basic_info, kgd_data, court_data, zakup_data, lic_data)
# Telegram имеет лимит на длину сообщения; если очень длинный текст — можно разрезать
MAX = 3900
if len(text) <= MAX:
await bot.send_message(chat_id, text, parse_mode="Markdown")
else:
# делим на куски по параграфам
parts = [text[i:i+MAX] for i in range(0, len(text), MAX)]
for p in parts:
await bot.send_message(chat_id, p, parse_mode="Markdown")




# Небольшой aiohttp сервер чтобы Render не завершал процесс
async def start_server():
app = web.Application()
async def health(request):
return web.Response(text="OK")
app.router.add_get('/', health)
runner = web.AppRunner(app)
await runner.setup()
site = web.TCPSite(runner, '0.0.0.0', PORT)
await site.start()
print(f"Health server started on port {PORT}")




async def main():
await start_server()
await dp.start_polling(bot)


if __name__ == '__main__':
try:
asyncio.run(main())
except (KeyboardInterrupt, SystemExit):
print('Bot stopped')
