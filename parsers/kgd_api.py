import requests

BASE_URL = "https://data.egov.kz/api/v4/"

# --- Поиск компании по БИН ---
def search_by_bin(bin_number: str):
    """
    Возвращает данные о компании по БИН из открытого источника KGD.
    """
    url = f"{BASE_URL}kgd_ul/v4?bin={bin_number}&source=gov"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if not data:
            return {"error": "Компания с таким БИН не найдена."}
        return data[0]
    except Exception as e:
        return {"error": str(e)}

# --- Поиск по названию компании ---
def search_by_name(name: str, limit: int = 5):
    """
    Возвращает до 5 компаний, найденных по названию.
    """
    url = f"{BASE_URL}kgd_ul/v4?ul_name__icontains={name}&source=gov"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data[:limit] if data else [{"message": "Ничего не найдено"}]
    except Exception as e:
        return [{"error": str(e)}]

# --- Проверка задолженности ---
def get_tax_debt(bin_number: str):
    """
    Проверяет наличие налоговой задолженности компании по БИН.
    """
    url = f"{BASE_URL}kgd_tax_arrear/v4?bin={bin_number}&source=gov"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if not data:
            return {"status": "Нет задолженности"}
        return {"status": "Есть задолженность", "details": data}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    # Примеры проверки
    print(search_by_bin("201240025834"))
    print(search_by_name("КазОйл"))
    print(get_tax_debt("201240025834"))
