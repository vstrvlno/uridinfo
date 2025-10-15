# parsers/stat_api.py
import aiohttp

STAT_SEARCH_URL = "https://stat.gov.kz/api/juridical/search"
STAT_DETAIL_URL = "https://stat.gov.kz/api/juridical"

async def _get_json(session: aiohttp.ClientSession, url: str, params: dict = None):
    try:
        async with session.get(url, params=params, timeout=20) as resp:
            if resp.status == 200:
                return await resp.json(content_type=None)
            else:
                return None
    except Exception:
        return None


async def search_by_name(name: str, limit: int = 5):
    """
    Поиск компаний по названию через API stat.gov.kz
    Возвращает список {name, bin}
    """
    async with aiohttp.ClientSession() as session:
        params = {
            "lang": "ru",
            "bin": "",
            "name": name,
            "region": "",
            "pageSize": limit,
            "pageNumber": 1
        }
        data = await _get_json(session, STAT_SEARCH_URL, params)
        if not data or not isinstance(data, list):
            return []

        results = []
        for it in data[:limit]:
            results.append({
                "name": it.get("name"),
                "bin": it.get("bin")
            })
        return results


async def search_by_bin(bin_: str):
    """
    Проверка существования компании по БИН (через поиск)
    """
    async with aiohttp.ClientSession() as session:
        params = {
            "lang": "ru",
            "bin": bin_,
            "name": "",
            "region": "",
            "pageSize": 1,
            "pageNumber": 1
        }
        data = await _get_json(session, STAT_SEARCH_URL, params)
        if not data or not isinstance(data, list):
            return None
        return data[0]


async def get_company_by_bin(bin_: str):
    """
    Получение полной информации по БИН.
    """
    async with aiohttp.ClientSession() as session:
        url = f"{STAT_DETAIL_URL}/{bin_}?lang=ru"
        data = await _get_json(session, url)
        if not data:
            return None

        # Формируем ключевые поля для карточки
        result = {
            "name": data.get("name"),
            "bin": data.get("bin"),
            "oked_name": data.get("okedName"),
            "oked": data.get("oked"),
            "address": data.get("address"),
            "registration_date": data.get("regDate"),
            "director": data.get("fio")
        }
        return result
