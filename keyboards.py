"""
keyboards.py — Barcha Telegram klaviaturalar (inline va reply)
"""

import json
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from telegram import Update

from config import CATEGORIES, UserState, CURRENCY
from database import get_user_state, get_temp_data, set_user_state, add_expense

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────
# Reply klaviatura (asosiy menyu)
# ─────────────────────────────────────────

def main_keyboard() -> ReplyKeyboardMarkup:
    """Asosiy menyu tugmalari."""
    buttons = [
        ["➕ Xarajat qo'shish", "📊 Hisobot"],
        ["🗑 Oxirginini o'chir"],
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


# ─────────────────────────────────────────
# Inline klaviatura — kategoriyalar
# ─────────────────────────────────────────

def category_keyboard() -> InlineKeyboardMarkup:
    """Kategoriya tanlash uchun inline klaviatura (2 ustun)."""
    from config import CATEGORIES
    buttons = []
    row = []
    for i, cat in enumerate(CATEGORIES):
        row.append(InlineKeyboardButton(cat, callback_data=f"cat:{cat}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("❌ Bekor qilish", callback_data="cat:cancel")])
    return InlineKeyboardMarkup(buttons)


# ─────────────────────────────────────────
# Inline klaviatura — hisobot opsiyalari
# ─────────────────────────────────────────

def report_keyboard() -> InlineKeyboardMarkup:
    """Hisobot sahifasida ko'rsatiladigan tugmalar."""
    buttons = [
        [InlineKeyboardButton("🤖 AI maslahat", callback_data="report:ai")],
        [InlineKeyboardButton("📋 Batafsil ro'yxat", callback_data="report:detail")],
        [InlineKeyboardButton("🔄 Yangilash", callback_data="report:refresh")],
    ]
    return InlineKeyboardMarkup(buttons)


# ─────────────────────────────────────────
# Callback query handler (barcha inline tugmalar)
# ─────────────────────────────────────────

async def button_callback_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Barcha inline tugma bosiqlari shu yerda qayta ishlanadi."""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    data = query.data

    # ── Kategoriya tanlash ──────────────────
    if data.startswith("cat:"):
        await _handle_category_selection(query, user_id, data[4:])

    # ── Hisobot tugmalari ───────────────────
    elif data.startswith("report:"):
        await _handle_report_action(query, user_id, data[7:])


# ─────────────────────────────────────────
# Kategoriya tanlash logikasi
# ─────────────────────────────────────────

async def _handle_category_selection(query, user_id: int, category: str) -> None:
    from config import CURRENCY

    if category == "cancel":
        set_user_state(user_id, UserState.IDLE)
        await query.edit_message_text("❌ Xarajat qo'shish bekor qilindi.")
        return

    state = get_user_state(user_id)
    if state != UserState.WAITING_CATEGORY:
        await query.edit_message_text("⚠️ Eski tugma. /add orqali qaytadan boshlang.")
        return

    temp_raw = get_temp_data(user_id)
    temp = json.loads(temp_raw)
    temp["category"] = category
    set_user_state(user_id, UserState.WAITING_NOTE, json.dumps(temp))

    await query.edit_message_text(
        f"📂 Kategoriya: <b>{category}</b>\n"
        f"💰 Summa: <b>{temp['amount']:,.0f} {CURRENCY}</b>\n\n"
        "📝 Izoh kiriting (ixtiyoriy):\n"
        "<i>O'tkazib yuborish uchun '-' yozing</i>",
        parse_mode="HTML",
    )


# ─────────────────────────────────────────
# Hisobot tugmalari logikasi
# ─────────────────────────────────────────

async def _handle_report_action(query, user_id: int, action: str) -> None:
    from reports import build_monthly_report_text
    from ai_helper import get_ai_advice
    from database import get_monthly_summary, get_monthly_expenses
    from datetime import datetime

    now = datetime.now()

    if action == "refresh":
        text = build_monthly_report_text(user_id, now.year, now.month)
        await query.edit_message_text(
            text, parse_mode="HTML",
            reply_markup=_report_keyboard_inline()
        )

    elif action == "ai":
        summary = get_monthly_summary(user_id, now.year, now.month)
        if not summary:
            await query.edit_message_text("📭 Tahlil uchun ma'lumot yo'q.")
            return
        await query.edit_message_text("⏳ AI tahlil qilyapti...")
        advice = await get_ai_advice(summary)
        await query.edit_message_text(
            f"🤖 <b>AI Maslahat:</b>\n\n{advice}",
            parse_mode="HTML",
        )

    elif action == "detail":
        expenses = get_monthly_expenses(user_id, now.year, now.month)
        if not expenses:
            await query.edit_message_text("📭 Bu oy xarajatlar yo'q.")
            return
        lines = ["📋 <b>Batafsil ro'yxat:</b>\n"]
        for e in expenses[:20]:  # max 20 ta
            date = e["created_at"][:10]
            lines.append(
                f"• {e['category']} — <b>{e['amount']:,.0f}</b> "
                f"<i>({date})</i>"
                + (f" — {e['note']}" if e["note"] else "")
            )
        if len(expenses) > 20:
            lines.append(f"\n<i>...va yana {len(expenses)-20} ta</i>")
        await query.edit_message_text("\n".join(lines), parse_mode="HTML")


def _report_keyboard_inline() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton("🤖 AI maslahat", callback_data="report:ai")],
        [InlineKeyboardButton("📋 Batafsil", callback_data="report:detail")],
        [InlineKeyboardButton("🔄 Yangilash", callback_data="report:refresh")],
    ]
    return InlineKeyboardMarkup(buttons)
