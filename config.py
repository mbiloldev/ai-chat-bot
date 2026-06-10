"""
config.py — Sozlamalar va konstantalar
"""

import os
from dotenv import load_dotenv

load_dotenv()

# === Token ===
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

# === Ma'lumotlar bazasi ===
DB_PATH: str = os.getenv("DB_PATH", "expenses.db")

# === Xarajat kategoriyalari ===
CATEGORIES: list[str] = [
    "🍔 Ovqat",
    "🚗 Transport",
    "🏠 Uy-joy",
    "👕 Kiyim",
    "💊 Sog'liq",
    "🎮 Ko'ngilochar",
    "📚 Ta'lim",
    "💼 Ish",
    "🛒 Bozor",
    "❓ Boshqa",
]

# Kategoriya emoji → sof nom mapping
CATEGORY_NAMES: dict[str, str] = {
    "🍔 Ovqat": "Ovqat",
    "🚗 Transport": "Transport",
    "🏠 Uy-joy": "Uy-joy",
    "👕 Kiyim": "Kiyim",
    "💊 Sog'liq": "Sog'liq",
    "🎮 Ko'ngilochar": "Ko'ngilochar",
    "📚 Ta'lim": "Ta'lim",
    "💼 Ish": "Ish",
    "🛒 Bozor": "Bozor",
    "❓ Boshqa": "Boshqa",
}

# === Valyuta ===
CURRENCY: str = "UZS"

# === AI prompt ===
AI_SYSTEM_PROMPT: str = (
    "Sen xarajat tahlilchisi bo'tsan. Foydalanuvchi xarajat ma'lumotlarini beradi, "
    "sen ularni tahlil qilib, qisqa va foydali maslahat berasan. "
    "Javobni o'zbek tilida, 3-5 jumlada ber. Raqamlarni minglik ajratgich bilan ko'rsat."
)

# === User holatlari (FSM) ===
class UserState:
    IDLE = "idle"
    WAITING_AMOUNT = "waiting_amount"
    WAITING_CATEGORY = "waiting_category"
    WAITING_NOTE = "waiting_note"
