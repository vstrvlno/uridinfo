# parsers/utils.py

def format_company_card(stat, kgd, zakup, lic):
    text = f"🏢 *{stat.get('name', 'Не найдено')}*\n\n"
    text += f"📍 Адрес: {stat.get('address', '-')}\n"
    text += f"📆 Регистрация: {stat.get('registration_date', '-')}\n"
    text += f"👨‍💼 Руководитель: {stat.get('director', '-')}\n"
    text += f"🏷️ ОКЭД: {stat.get('oked_name', '-')}\n\n"

    text += f"💰 Налоги: {kgd.get('tax_paid', '-')}\n"
    text += f"🚨 Задолженность: {kgd.get('debt', '-')}\n"
    text += f"⚠️ Риск: {kgd.get('risk_level', '-')}\n\n"

    text += f"📄 Госзакупки: {len(zakup)}\n"
    text += f"🧾 Лицензии: {len(lic)}\n"
    return text
