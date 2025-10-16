import aiohttp

API_URL = "https://data.egov.kz/api/v4/gbd_ul/v2"

async def search_company(name: str):
    """Поиск компании по названию или БИН через API data.egov.kz"""
    try:
        async with aiohttp.ClientSession() as session:
            params = {
                "query": name,
                "size": 1
            }
            async with session.get(API_URL, params=params, timeout=15) as resp:
                if resp.status != 200:
                    return f"⚠️ Ошибка подключения: {resp.status}"
                
                data = await resp.json()

                if not data:
                    return "❌ Компания не найдена."

                company = data[0]

                # Обрабатываем возможные варианты ключей
                name_ru = company.get("name_ru") or company.get("name_kz") or "Не найдено"
                bin_code = company.get("bin", "Не найдено")
                address = company.get("legal_address", "-")
                reg_date = company.get("reg_date", "-")
                activity = company.get("okved_name", "-")
                director = company.get("fio_rykovoditelya", "-")

                result = (
                    f"🏢 <b>Название:</b> {name_ru}\n"
                    f"📇 <b>БИН:</b> {bin_code}\n"
                    f"📍 <b>Адрес:</b> {address}\n"
                    f"📅 <b>Регистрация:</b> {reg_date[:10] if reg_date != '-' else '-'}\n"
                    f"💼 <b>Вид деятельности:</b> {activity}\n"
                    f"👤 <b>Руководитель:</b> {director}"
                )

                return result

    except Exception as e:
        return f"⚠️ Ошибка: {e}"
