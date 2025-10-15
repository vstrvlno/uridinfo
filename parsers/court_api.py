import aiohttp
import asyncio

BASE_URL = "https://office.sud.kz/api/process/search"

async def get_court_cases(query: str, limit: int = 5) -> list:
    """
    Получает список судебных дел по названию компании или БИН.
    query — строка поиска (название компании или БИН)
    limit — ограничение количества результатов (по умолчанию 5)
    """
    params = {
        "page": 1,
        "size": limit,
        "query": query
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(BASE_URL, params=params, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    if not data.get("content"):
                        return [{"error": "Судебные дела не найдены."}]
                    return [parse_case(c) for c in data.get("content", [])]
                else:
                    return [{"error": f"Ошибка API ({response.status})"}]
    except asyncio.TimeoutError:
        return [{"error": "Время ожидания запроса истекло."}]
    except Exception as e:
        return [{"error": f"Ошибка при запросе: {str(e)}"}]


def parse_case(case: dict) -> dict:
    """
    Преобразует данные судебного дела в удобный формат.
    """
    return {
        "Номер дела": case.get("
