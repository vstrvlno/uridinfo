import aiohttp
import asyncio
import json

BASE_URL = "https://data.egov.kz/api/v4"

# --- Список API наборов данных ---
DATASETS = {
    "company": "reestr_yuridicheskikh_lits/v1",
    "nds": "nds_registraciya/v1",
    "license": "licenzii_i_razresheniya/v1",
    "court": "sudebnye_dela/v1",
    "exec": "ispolnitelnoe_proizvodstvo/v1",
    "zakup": "gos_zakup_uchastniki/v1",
    "stats": "stat_predpriyatiya/v1"
}


async def fetch_json(session, url):
    """Асинхронно получает JSON с API data.egov.kz"""
    try:
        async with session.get(url, timeout=15) as response:
            if response.status == 200:
                data = await response.text()
                try:
                    return json.loads(data)
                except json.JSONDecodeError:
                    return None
            else:
                print(f"Ошибка: {url} — {response.status}")
                return None
    except Exception as e:
        print(f"Ошибка при запросе {url}: {e}")
        return None


async def search_company(query):
    """
    Универсальный поиск по названию или БИН компании.
    Возвращает объединённый результат из всех доступных API.
    """
    async with aiohttp.ClientSession() as session:
        results = {}

        for key, endpoint in DATASETS.items():
            url = f"{BASE_URL}/{endpoint}?source=" + json.dumps({
                "query": {
                    "bool": {
                        "should": [
                            {"match_phrase": {"bin": query}},
                            {"match_phrase": {"company_name": query}},
                            {"match_phrase": {"name": query}}
                        ]
                    }
                },
                "size": 5
            }, ensure_ascii=False)

            data = await fetch_json(session, url)
            results[key] = data if data else []

        return results


def format_result(data):
    """Форматирует результат для вывода пользователю в Telegram."""
    text = "🏢 *Информация о компании:*\n\n"

    # --- Основные сведения ---
    company = data.get("company", [])
    if company:
        c = company[0]
        text += f"**{c.get('name', '-') }**\n"
        text += f"БИН: `{c.get('bin', '-')}`\n"
        text += f"Адрес: {c.get('address', '-')}\n"
        text += f"Дата регистрации: {c.get('registration_date', '-')}\n"
        text += f"Руководитель: {c.get('director', '-')}\n\n"
    else:
        text += "❌ Компания не найдена\n\n"

    # --- НДС ---
    nds = data.get("nds", [])
    if nds:
        n = nds[0]
        text += f"💰 *НДС:* {n.get('status', '-')}\n\n"

    # --- Судебные дела ---
    court = data.get("court", [])
    if court:
        text += f"⚖️ Судебные дела: {len(court)}\n"
        for c in court[:3]:
            text += f"  • {c.get('case_number', '-')}: {c.get('case_status', '-')}\n"
        text += "\n"

    # --- Исполнительные производства ---
    execs = data.get("exec", [])
    if execs:
        text += f"🔒 Исполнительные производства: {len(execs)}\n\n"

    # --- Госзакупки ---
    zakup = data.get("zakup", [])
    if zakup:
        text += f"📄 Госзакупки: {len(zakup)} записей\n\n"

    # --- Лицензии ---
    lic = data.get("license", [])
    if lic:
        text += f"🧾 Лицензии: {len(lic)}\n\n"

    # --- Статистика ---
    stats = data.get("stats", [])
    if stats:
        s = stats[0]
        text += f"📊 Размер предприятия: {s.get('company_size', '-')}\n"
        text += f"📈 Оборот: {s.get('turnover', '-')}\n\n"

    return text


# --- Тест локально ---
if __name__ == "__main__":
    async def main():
        query = "КазОйлГрупп"
        data = await search_company(query)
        print(format_result(data))

    asyncio.run(main())
