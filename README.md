# 💰 Expense Tracker Telegram Bot

AI-powered xarajat kuzatuvchi Telegram bot (Python + OpenAI)

## 📁 Fayl tuzilmasi

```
expense_bot/
├── main.py          # Bot ishga tushiruvchi, handler ro'yxati
├── config.py        # Sozlamalar, konstantalar, UserState
├── database.py      # SQLite CRUD operatsiyalar
├── handlers.py      # /start /help /add + FSM logika
├── keyboards.py     # Inline va Reply klaviaturalar + callback
├── reports.py       # Oylik hisobot generatsiyasi
├── ai_helper.py     # OpenAI integratsiya (tahlil, maslahat)
├── requirements.txt
└── .env.example
```

markdown<div align="center">
  <img src="./banner.svg" width="100%"/>
</div>

## 🚀 Ishga tushirish

```bash
# 1. Paketlarni o'rnatish
pip install -r requirements.txt

# 2. .env faylini sozlash
cp .env.example .env
# .env ichiga BOT_TOKEN va OPENAI_API_KEY kiriting

# 3. Botni ishga tushirish
python main.py
```

## ⚙️ Sozlash

`.env` faylini to'ldiring:
```
BOT_TOKEN=BotFather dan olingan token
OPENAI_API_KEY=OpenAI kaliti (ixtiyoriy)
```

## 🤖 Komandalar

| Komanda | Tavsif |
|---------|--------|
| `/start` | Botni boshlash |
| `/add` | Xarajat qo'shish |
| `/report` | Oylik hisobot |
| `/help` | Yordam |

## 🛠 Texnologiyalar

- `python-telegram-bot` — Telegram Bot API
- `openai` — AI tahlil va maslahat
- `sqlite3` — Ma'lumotlar bazasi (built-in)
- `python-dotenv` — Environment variables
