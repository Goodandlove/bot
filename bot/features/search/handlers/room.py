# bot\features\search\handlers\room.py

import logging
from telegram import Update
from telegram.ext import ContextTypes
from bot.core.redis_manager import RedisManager
from bot.core.states import States
from bot.presentation.keyboards.search import price_selection
from bot.data.repositories.user import log_user_action
from bot.presentation.keyboards.search import room_selection


logger = logging.getLogger(__name__)

async def handle_room_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора количества комнат"""
    user = update.effective_user
    room_choice = update.message.text
    
    # Проверяем, что выбор корректен
    valid_choices = ['1', '2', '3', '4+', 'Студия']
    if room_choice not in valid_choices:
        await update.message.reply_text(
            "❌ Пожалуйста, выберите один из предложенных вариантов комнат",
            reply_markup=room_selection()
        )
        return
    
    # Сохраняем выбор комнат
    RedisManager().set_search_data(user.id, 'rooms', room_choice)
    RedisManager().set_state(user.id, States.SEARCH_PRICE)
    log_user_action(user.id, user.full_name, f"Выбор комнат: {room_choice}")
    
    await update.message.reply_text(
        "🔢 *Этап 2: Цена (в тысячах рублей)*\n\n"
        "Укажите ценовой диапазон поиска\n",
        reply_markup=price_selection(),
        parse_mode='Markdown'
    )