"""
ai_helper.py — OpenAI orqali AI tahlil va kategoriyalash
"""

import logging
import json
from openai import AsyncOpenAI
from config import OPENAI_API_KEY, AI_SYSTEM_PROMPT, CURRENCY

logger = logging.getLogger(__name__)
client = AsyncOpenAI(api_key=OPENAI_API_KEY)


# ─────────────────────────────────────────
# Kategoriyani taxmin qilish
# ─────────────────────────────────────────

async def categorize_expense(note: str, categories: list[str]) -> str | None:
    """
    Izoh asosida eng mos kategoriyani qaytaradi.
    Agar aniqlab bo'lmasa None qaytaradi.
    """
    if not OPENAI_API_KEY or not note:
        return None

    prompt = (
        f"Quyidagi xarajat izohi uchun eng mos kategoriyani tanlang:\n"
        f"Izoh: '{note}'\n\n"
        f"Kategoriyalar: {', '.join(categories)}\n\n"
        f"Faqat bitta kategoriya nomini yozing, boshqa narsa yozmang."
    )

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Sen xarajat kategoriyalash assistantisan."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=30,
            temperature=0.2,
        )
        result = response.choices[0].message.content.strip()
        # Ro'yxatdan tekshirish
        for cat in categories:
            if cat.lower() in result.lower() or result.lower() in cat.lower():
                return cat
        return None
    except Exception as e:
        logger.error(f"Kategoriyalash xatosi: {e}")
        return None


# ─────────────────────────────────────────
# Oylik tahlil va maslahat
# ─────────────────────────────────────────

async def get_ai_advice(summary: list[dict]) -> str:
    """
    Oylik xarajat xulosasi asosida AI maslahat qaytaradi.
    """
    if not OPENAI_API_KEY:
        return (
            "⚠️ AI maslahat uchun OPENAI_API_KEY kerak.\n"
            ".env faylga kalit kiriting."
        )

    # Xulosa matnini tayyorlash
    summary_text = "\n".join(
        f"- {row['category']}: {row['total']:,.0f} {CURRENCY} ({row['count']} ta xarajat)"
        for row in summary
    )
    total = sum(row["total"] for row in summary)

    user_message = (
        f"Bu oy xarajatlarim:\n{summary_text}\n\n"
        f"Jami: {total:,.0f} {CURRENCY}\n\n"
        "Menga moliyaviy maslahat ber."
    )

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": AI_SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            max_tokens=300,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"AI maslahat xatosi: {e}")
        return f"❌ AI xizmatida xatolik: {str(e)}"


# ─────────────────────────────────────────
# Xarajatni matndan ajratib olish
# ─────────────────────────────────────────

async def parse_expense_from_text(text: str) -> dict | None:
    """
    Erkin matndan xarajat ma'lumotlarini ajratadi.
    Masalan: 'kechagi kino uchun 30000 to'ladim' → {amount: 30000, category: '🎮 Ko'ngilochar'}
    Qaytaradi: {'amount': float, 'category': str, 'note': str} yoki None
    """
    if not OPENAI_API_KEY:
        return None

    prompt = (
        f"Quyidagi matndan xarajat ma'lumotlarini ajrat:\n"
        f"Matn: '{text}'\n\n"
        f"JSON formatda qaytargin (faqat JSON, boshqa narsa yozma):\n"
        f'{{"amount": <raqam>, "category": "<kategoriya>", "note": "<izoh>"}}\n\n'
        f"Agar xarajat ma'lumoti yo'q bo'lsa: null"
    )

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Sen matndan xarajat ajratuvchi assistantisan."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=100,
            temperature=0.1,
        )
        raw = response.choices[0].message.content.strip()
        if raw.lower() == "null":
            return None
        # JSON fences tozalash
        raw = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(raw)
    except Exception as e:
        logger.error(f"Matn tahlili xatosi: {e}")
        return None
