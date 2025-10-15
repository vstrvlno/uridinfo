# parsers/licenses_api.py
import aiohttp

async def get_licenses_info(query: str):
    """
    Получает информацию о лицензиях компании по БИН или названию.
    """
    url = f"https://elicense.kz/api/clients/search?text={query}&size=5"
    headers = {"Accept": "application/json"}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status != 200:
                return []
            data = await resp.json()

    results = []
    for item in data.get("items", []):
        results.append({
            "name": item.get("name_ru"),
            "bin": item.get("bin"),
            "activity": item.get("activity_name_ru"),
            "status": item.get("status_name_ru"),
            "license_number": item.get("license_number")
        })
    return results
