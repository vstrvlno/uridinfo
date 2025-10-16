# parsers/utils.py

def is_bin(text: str) -> bool:
    """
    Проверяет, является ли строка БИН (12 цифр).
    """
    return text.isdigit() and len(text) == 12


def format_full_card(stat, kgd, court, zakup, lic):
    """
    Формирует подробную карточку компании с данными из всех источников.
    """
    text = f"🏢 *{stat.get('name', 'Не найдено')}*\n\n"
    text += f"📍 Адрес: {stat.get('address', '-')}\n"
    text += f"📆 Регистрация: {stat.get('registration_date', '-')}\n"
    text += f"👨‍💼 Руководитель: {stat.get('director', '-')}\n"
    text += f"🏷️ ОКЭД: {stat.get('oked_name', '-')}\n\n"

    text += f"💰 Налоги: {kgd.get('tax_paid', '-')}\n"
    text += f"🚨 Задолженность: {kgd.get('debt', '-')}\n"
    text += f"⚠️ Риск: {kgd.get('risk_level', '-')}\n\n"

    # Судебные дела
    if isinstance(court, list) and court:
        text += "⚖️ Судебные дела:\n"
        for c in court[:3]:  # максимум 3 дела для краткости
            num = c.get("Номер дела", "-")
            cat = c.get("Категория", "-")
            date = c.get("Дата", "-")
            text += f"• {num} ({cat}, {date})\n"
    else:
        text += "⚖️ Судебные дела: не найдены\n"

    text += "\n📄 Госзакупки: " + str(len(zakup) if isinstance(zakup, list) else 0)
    text += "\n🧾 Лицензии: " + str(len(lic) if isinstance(lic, list) else 0)

    return text
