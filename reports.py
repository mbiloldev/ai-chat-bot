"""
reports.py — Oylik hisobot generatsiyasi
"""

import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

from config import CURRENCY
from database import get_monthly_summary, get_all_time_total
from keyboards import _report_keyboard_inline

logger = logging.getLogger(__name__)

# Uzbek oy nomlari
MONTH_NAMES = {
    1: "Yanvar", 2: "Fevral", 3: "Mart", 4: "Aprel",
    5: "May", 6: "Iyun", 7: "Iyul", 8: "Avgust",
    9: "Sentabr", 10: "Oktabr", 11: "Noyabr", 12: "Dekabr",
}


# ─────────────────────────────────────────
# /report komandasi
# ─────────────────────────────────────────

async def report_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    now = datetime.now()

    text = build_monthly_report_text(user_id, now.year, now.month)

    await update.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=_report_keyboard_inline(),
    )


# ─────────────────────────────────────────
# Hisobot matni yaratish
# ─────────────────────────────────────────

def build_monthly_report_text(user_id: int, year: int, month: int) -> str:
    """
    Berilgan yil va oy uchun HTML formatdagi hisobot matni.
    """
    summary = get_monthly_summary(user_id, year, month)
    month_name = MONTH_NAMES.get(month, str(month))
    total_all_time = get_all_time_total(user_id)

    if not summary:
        return (
            f"📊 <b>{month_name} {year} hisoboti</b>\n\n"
            "📭 Bu oy hech qanday xarajat kiritilmagan.\n\n"
            "➕ /add orqali birinchi xarajatni qo'shing!"
        )

    month_total = sum(row["total"] for row in summary)
    lines = [
        f"📊 <b>{month_name} {year} Hisoboti</b>",
        f"━━━━━━━━━━━━━━━━━━",
    ]

    # Kategoriyalar bo'yicha
    for row in summary:
        cat = row["category"]
        total = row["total"]
        count = row["count"]
        percent = (total / month_total * 100) if month_total else 0
        bar = _progress_bar(percent)

        lines.append(
            f"\n{cat}\n"
            f"  {bar} {percent:.0f}%\n"
            f"  💵 {total:,.0f} {CURRENCY}  ({count} ta)"
        )

    lines += [
        f"\n━━━━━━━━━━━━━━━━━━",
        f"📅 <b>Bu oy jami:</b> {month_total:,.0f} {CURRENCY}",
        f"🗓 <b>Hammasi bo'lib:</b> {total_all_time:,.0f} {CURRENCY}",
        f"\n<i>🔄 Yangilash tugmasini bosing</i>",
    ]

    return "\n".join(lines)


# ─────────────────────────────────────────
# Yordamchi funksiyalar
# ─────────────────────────────────────────

def _progress_bar(percent: float, length: int = 10) -> str:
    """Matnli progress bar. Masalan: ████░░░░░░ 40%"""
    filled = round(percent / 100 * length)
    empty = length - filled
    return "█" * filled + "░" * empty
