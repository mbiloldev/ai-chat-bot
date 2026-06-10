"""
main.py — Bot ishga tushiruvchi fayl
"""

import logging
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from config import BOT_TOKEN
from handlers import (
    start_handler,
    help_handler,
    add_expense_handler,
    text_message_handler,
)
from reports import report_handler
from keyboards import button_callback_handler

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main():
    logger.info("Bot ishga tushmoqda...")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Komandalar
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(CommandHandler("add", add_expense_handler))
    app.add_handler(CommandHandler("report", report_handler))

    # Inline tugmalar
    app.add_handler(CallbackQueryHandler(button_callback_handler))

    # Oddiy matn xabarlari
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message_handler))

    logger.info("Handlerlar ro'yxatdan o'tdi. Polling boshlandi.")
    app.run_polling()


if __name__ == "__main__":
    main()
