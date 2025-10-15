# parsers/utils.py
from typing import List


BIN_RE = re.compile(r"^\d{12}$")


def is_bin(s: str) -> bool:
s = s.strip()
return bool(BIN_RE.match(s))




def format_money(val) -> str:
try:
v = float(val)
return f"{v:,.2f}"
except Exception:
return str(val)




def format_full_card(basic: dict, kgd: dict, court: List[dict], zakup: List[dict], lic: List[dict]) -> str:
# Собирает markdown-текст карточки
lines = []
name = basic.get('name') or basic.get('title') or '-'
bin_ = basic.get('bin') or basic.get('BIN') or '-'
addr = basic.get('address') or '-'
reg_date = basic.get('registration_date') or basic.get('reg_date') or '-'
director = basic.get('director') or '-'
oked = basic.get('oked_name') or basic.get('oked') or '-'


lines.append(f"*{name}* \nБИН: `{bin_}`")
lines.append(f"📍 Адрес: {addr}")
lines.append(f"📆 Регистрация: {reg_date}")
lines.append(f"👨‍💼 Руководитель: {director}")
lines.append(f"🏷️ ОКЭД: {oked}\n")


# Налоги
tax_sum = kgd.get('tax_paid') or kgd.get('paid') or '-'
debt = kgd.get('debt') or kgd.get('tax_debt') or '-'
risk = kgd.get('risk_level') or kgd.get('risk') or '-'
lines.append(f"💰 Налоги (платежи): {tax_sum}")
lines.append(f"🚨 Задолженность: {debt}")
lines.append(f"⚠️ Уровень риска: {risk}\n")


# Судебные дела
lines.append(f"⚖️ Судебных дел: {len(court)}")
for c in court[:5]:
title = c.get('title') or c.get('case_title') or c.get('subject') or '-'
date = c.get('date') or c.get('decision_date') or '-'
lines.append(f"• {title} — {date}")
lines.append('\n')


# Госзакупки
lines.append(f"📄 Госзакупок: {len(zakup)}")
for z in zakup[:5]:
t = z.get('title') or z.get('lot_title') or '-'
year = z.get('year') or z.get('date') or '-'
lines.append(f"• {t} — {year}")
lines.append('\n')


# Лицензии
lines.append(f"🧾 Лицензий/разрешений: {len(lic)}")
for l in lic[:5]:
ln = l.get('name') or l.get('license_name') or '-'
exp = l.get('expiry') or l.get('end_date') or '-'
lines.append(f"• {ln} — {exp}")
lines.append('\n')


# Доп. сведения
lines.append("---")
lines.append("_Данные получены из открытых источников. Обновление — в режиме реального времени (без кеша)._")


return "\n".join(lines)
