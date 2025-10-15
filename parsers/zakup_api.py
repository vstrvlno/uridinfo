# parsers/zakup_api.py
import aiohttp

BASE_URL = "https://ows.goszakup.gov.kz/v3/graphql"

async def get_goszakup_info(query: str):
    """
    Получает список госзакупок по БИН или названию компании.
    """
    url = f"https://ows.goszakup.gov.kz/v3/subject/search?search={query}&page=1&size=5"
    headers = {
        "Accept": "application/json"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status != 200:
                return []
            data = await resp.json()

    results = []
    for item in data.get("items", []):
        results.append({
            "bin": item.get("bin"),
            "name": item.get("name_ru") or item.get("name_kz"),
            "region": item.get("region_name_ru"),
            "id": item.get("id")
        })
    return results
