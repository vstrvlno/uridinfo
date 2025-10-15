# parsers/stat_api.py
import aiohttp
import asyncio


# ВАЖНО: реальные конечные точки API могут отличаться. Здесь шаблон с понятным интерфейсом.


STAT_BASE = 'https://stat.gov.kz' # при необходимости обновить


async def _get_json(session: aiohttp.ClientSession, url: str, params: dict = None):
try:
async with session.get(url, params=params, timeout=15) as resp:
if resp.status == 200:
return await resp.json()
else:
return None
except Exception:
return None




async def search_by_name(name: str, limit: int = 5):
"""Ищет компании по названию, возвращает список словарей с как минимум keys: name, bin"""
url = f"{STAT_BASE}/api/search" # заменить на реальный endpoint
params = {'q': name, 'limit': limit}
async with aiohttp.ClientSession() as s:
data = await _get_json(s, url, params=params)
if not data:
return []
# Трансформируем в ожидаемый формат
results = []
items = data.get('results') if isinstance(data, dict) else data
for it in items[:limit]:
results.append({
'name': it.get('name') or it.get('title'),
'bin': it.get('bin') or it.get('BIN') or it.get('iik')
})
return results
data = await _ge
