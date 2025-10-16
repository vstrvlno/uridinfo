import aiohttp
import logging
import urllib.parse
import os

API_KEY = os.getenv("EGOV_API_KEY")  # твой ключ из .env
BASE_URL = "https://data.egov.kz/api/v4"

# ID нужных наборов данных (dataset)
DATASETS = {
    "companies": "gbd_ul",             # Основные сведения о юр. лицах
    "licenses": "reestr_licenziy",                 # Лицензии
    "goszakup": "gosudarstvennye_zakupki",        # Госзакупки
    "tax": "nalogovye_nachisleniya_i_platezhi"    # Налоги
}

async def fetch_json(session, url):
    try:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.json(content_type=None)
            else:
                logging.error(f"Ошибка {response.status} при загрузке {url}")
                return None
    except Exception as e:
        logging.error(f"Ошибка при загрузке {url}: {e}")
        return None


async def get_company_data(query: str):
    """Ищет данные компании по БИН или названию"""
    encoded_query = urllib.parse.quote(query)
    async with aiohttp.ClientSession() as session:
        dataset = DATASETS["companies"]
        url = f"{BASE_URL}/{dataset}?apiKey={API_KEY}&query={encoded_query}"
        data = await fetch_json(session, url)

        if not data or len(data) == 0:
            return None

        item = data[0]
        return {
            "name": item.get("naimenovanie_rus", "Не найдено"),
            "bin": item.get("bin", "-"),
            "address": item.get("yur_adres_rus", "-"),
            "registration_date": item.get("data_registracii", "-"),
            "oked_name": item.get("vid_deyatelnosti", "-"),
            "director": item.get("fio_rukovoditelya", "-")
        }
