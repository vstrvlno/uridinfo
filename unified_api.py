import aiohttp
import asyncio
import logging
import os

EGOV_TOKEN = os.getenv("EGOV_TOKEN")

BASE_URLS = [
    # Главный источник — API data.egov.kz
    f"https://data.egov.kz/api/v4/companies/v1?access_token={EGOV_TOKEN}",
    # При желании можно добавить сюда другие API с JSON данными
]


async def fetch_json(session, url):
    """Асинхронная загрузка JSON"""
    try:
        async with session.get(url, timeout=15) as response:
            if response.status == 200:
                return await response.json()
            else:
                logging.warning(f"Ошибка {response.status} при запросе {url}")
                return None
    except Exception as e:
        logging.error(f"Ошибка при загрузке {url}: {e}")
        return None


async def search_company(name: str):
    """Поиск компании по названию через все API"""
    async with aiohttp.ClientSession() as session:
        for base_url in BASE_URLS:
            url = f"{base_url}&query={name}"
            data = await fetch_json(session, url)
            if not data:
                continue

            # data может быть списком или словарем
            companies = data if isinstance(data, list) else data.get("companies", [])
            if not companies:
                continue

            for company in companies:
                if name.lower() in str(company).lower():
                    return format_company_info(company)

    return None


def format_company_info(company: dict) -> str:
    """Форматирует данные компании"""
    name = company.get("name", "—")
    bin_iin = company.get("bin", company.get("iin", "—"))
    reg_date = company.get("registration_date", "—")
    status = company.get("status", "—")
    address = company.get("address", "—")
    head = company.get("head", "—")
    risk = company.get("risk_level", "—")
    taxpayer = "Да" if company.get("nds_payer") else "Нет"
    activity = company.get("okved", "—")

    return (
        f"🏢 <b>{name}</b>\n"
        f"БИН/ИИН: <code>{bin_iin}</code>\n"
        f"📅 Дата регистрации: {reg_date}\n"
        f"📍 Адрес: {address}\n"
        f"👔 Руководитель: {head}\n"
        f"💼 Статус: {status}\n"
        f"📊 Плательщик НДС: {taxpayer}\n"
        f"⚖️ Уровень риска: {risk}\n"
        f"🔹 Вид деятельности: {activity}"
    )


# Тест ручного запуска
if __name__ == "__main__":
    async def main():
        result = await search_company("КазОйлГрупп-2009")
        print(result or "Компания не найдена")

    asyncio.run(main())
