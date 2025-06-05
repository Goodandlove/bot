# bot\features\search\handlers\start.py

import logging
from telegram import Update
from telegram.ext import ContextTypes
from bot.features.search.services import SearchService
from bot.presentation.keyboards.search import room_selection
from bot.presentation.keyboards.common import main_menu

logger = logging.getLogger(__name__)

async def start_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало процесса поиска"""
    user = update.effective_user
    if await SearchService.start_search(user):
        await update.message.reply_text(
            "🏠 *Поиск недвижимости*\n\n"
            "Давайте подберем для вас идеальный вариант!\n"
            "Сначала выберите количество комнат:",
            reply_markup=room_selection(),
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "⚠️ Произошла ошибка при запуске поиска. Попробуйте позже.",
            reply_markup=main_menu()
        )