import aiohttp
import asyncio

BASE_URL = "https://kgd.gov.kz/apps/services/culs-search-taxpayer/bin/"

async def get_company_info_by_bin(bin_number: str) -> dict:
    """
    Получает информацию о компании по БИН через официальный API КГД Казахстана.
    """
    url = f"{BASE_URL}{bin_number}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    if not data:
                        return {"error": "Данные не найдены."}
                    return parse_kgd_data(data)
                else:
                    return {"error": f"Ошибка API ({response.status})"}
    except asyncio.TimeoutError:
        return {"error": "Время ожидания запроса истекло."}
    except Exception as e:
        return {"error": f"Ошибка при запросе: {str(e)}"}


def parse_kgd_data(data: dict) -> dict:
    """
    Преобразует исходный JSON от КГД в удобный формат.
    """
    try:
        result = data.get("content", [])[0]
        return {
            "БИН": result.get("bin", "-"),
            "Наименование": result.get("name", "-"),
            "Регион": result.get("region", "-"),
            "Статус": result.get("taxpayerStatus", "-"),
            "Дата регистрации": result.get("regDate", "-"),
            "Риск": result.get("riskDegree", "-"),
            "НДС": result.get("vatRegistrationStatus", "-"),
            "Задолженность": result.get("taxArrears", "-"),
        }
    except Exception:
        return {"error": "Ошибка обработки данных."}


# Пример локального теста
if __name__ == "__main__":
    async def main():
        bin_number = "200940021948"  # пример БИН
        info = await get_company_info_by_bin(bin_number)
        print(info)

    asyncio.run(main())
