"""
handlers.py — Barcha komanda va xabar handlerlari
"""

import json
import logging
from telegram import Update
from telegram.ext import ContextTypes

from config import CATEGORIES, UserState, CURRENCY
from database import (
    upsert_user,
    add_expense,
    get_user_state,
    set_user_state,
    get_temp_data,
    delete_last_expense,
    init_db,
)
from keyboards import category_keyboard, main_keyboard
from ai_helper import categorize_expense, get_ai_advice

logger = logging.getLogger(__name__)

# DB ni ishga tushirish
init_db()


# ─────────────────────────────────────────
# /start
# ─────────────────────────────────────────

async def start_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    upsert_user(user.id, user.username or "", user.full_name)
    set_user_state(user.id, UserState.IDLE)

    text = (
        f"👋 Salom, <b>{user.first_name}</b>!\n\n"
        "Men sizning xarajatlaringizni kuzatib boraman 💰\n\n"
        "<b>Qanday foydalanish:</b>\n"
        "• /add — yangi xarajat qo'shish\n"
        "• /report — oylik hisobot\n"
        "• /help — yordam\n\n"
        "Yoki pastdagi tugmalardan foydalaning 👇"
    )
    await update.message.reply_text(
        text, parse_mode="HTML", reply_markup=main_keyboard()
    )


# ─────────────────────────────────────────
# /help
# ─────────────────────────────────────────

async def help_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "📖 <b>Yordam</b>\n\n"
        "<b>Komandalar:</b>\n"
        "• /start — botni qayta ishga tushirish\n"
        "• /add — xarajat qo'shish\n"
        "• /report — oylik hisobot ko'rish\n\n"
        "<b>Xarajat qo'shish tartibi:</b>\n"
        "1️⃣ /add ni bosing\n"
        "2️⃣ Summa kiriting (masalan: 50000)\n"
        "3️⃣ Kategoriya tanlang\n"
        "4️⃣ Izoh yozing (ixtiyoriy)\n\n"
        "<b>Qo'shimcha:</b>\n"
        "• 🗑 Oxirgi yozuvni o'chirish uchun tugmani bosing\n"
        "• 🤖 AI tahlil uchun /report dan keyin 'AI maslahat' tugmasini bosing"
    )
    await update.message.reply_text(text, parse_mode="HTML")


# ─────────────────────────────────────────
# /add — xarajat qo'shish bosqichi 1
# ─────────────────────────────────────────

async def add_expense_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    set_user_state(user_id, UserState.WAITING_AMOUNT)

    await update.message.reply_text(
        "💵 Xarajat summasini kiriting:\n"
        "<i>Misol: 50000 yoki 150000.50</i>",
        parse_mode="HTML",
    )


# ─────────────────────────────────────────
# Matn xabarlari — FSM (Finite State Machine)
# ─────────────────────────────────────────

async def text_message_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    text = update.message.text.strip()
    state = get_user_state(user_id)

    # --- Tugma orqali kelgan buyruqlar ---
    if text == "➕ Xarajat qo'shish":
        await add_expense_handler(update, ctx)
        return
    if text == "📊 Hisobot":
        from reports import report_handler
        await report_handler(update, ctx)
        return
    if text == "🗑 Oxirginini o'chir":
        await undo_last_handler(update, ctx)
        return

    # --- FSM holatlari ---
    if state == UserState.WAITING_AMOUNT:
        await _handle_amount(update, user_id, text)

    elif state == UserState.WAITING_NOTE:
        await _handle_note(update, user_id, text)

    else:
        await update.message.reply_text(
            "Buyruk tushunilmadi. /help yordam uchun.",
            reply_markup=main_keyboard(),
        )


# ─────────────────────────────────────────
# FSM — Summa kiritish
# ─────────────────────────────────────────

async def _handle_amount(update: Update, user_id: int, text: str) -> None:
    try:
        amount = float(text.replace(",", ".").replace(" ", ""))
        if amount <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text(
            "❌ Noto'g'ri format. Iltimos, raqam kiriting.\n"
            "<i>Misol: 50000</i>",
            parse_mode="HTML",
        )
        return

    # AI orqali kategoriyani taxmin qilish (agar izoh berilmagan bo'lsa)
    temp = json.dumps({"amount": amount})
    set_user_state(user_id, UserState.WAITING_CATEGORY, temp)

    await update.message.reply_text(
        f"✅ Summa: <b>{amount:,.0f} {CURRENCY}</b>\n\n"
        "📂 Kategoriyani tanlang:",
        parse_mode="HTML",
        reply_markup=category_keyboard(),
    )


# ─────────────────────────────────────────
# FSM — Izoh kiritish
# ─────────────────────────────────────────

async def _handle_note(update: Update, user_id: int, text: str) -> None:
    note = text if text.lower() not in ("-", "yo'q", "skip") else ""
    temp_raw = get_temp_data(user_id)
    temp = json.loads(temp_raw)
    temp["note"] = note

    expense_id = add_expense(
        user_id,
        temp["amount"],
        temp["category"],
        note,
    )

    set_user_state(user_id, UserState.IDLE)

    await update.message.reply_text(
        f"✅ <b>Xarajat saqlandi!</b>\n\n"
        f"💰 Summa: <b>{temp['amount']:,.0f} {CURRENCY}</b>\n"
        f"📂 Kategoriya: {temp['category']}\n"
        f"📝 Izoh: {note or '—'}\n"
        f"🆔 ID: #{expense_id}",
        parse_mode="HTML",
        reply_markup=main_keyboard(),
    )


# ─────────────────────────────────────────
# Oxirgi xarajatni o'chirish
# ─────────────────────────────────────────

async def undo_last_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    deleted = delete_last_expense(user_id)

    if deleted:
        await update.message.reply_text(
            "🗑 Oxirgi xarajat o'chirildi.",
            reply_markup=main_keyboard(),
        )
    else:
        await update.message.reply_text(
            "❌ O'chirish uchun xarajat topilmadi.",
            reply_markup=main_keyboard(),
        )
