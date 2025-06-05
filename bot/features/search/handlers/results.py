# bot/features/search/handlers/results.py 
# отображения следующей порции результатов поиска: 

import logging
from telegram import Update
from telegram.ext import ContextTypes
from bot.core.redis_manager import RedisManager
from bot.presentation.cards.search import format_property_card
from bot.presentation.keyboards.common import navigation_keyboard, details_keyboard
from config import Config
from bot.core.states import States
 

logger = logging.getLogger(__name__)

async def show_next_properties(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                              start_index: int, results: list):
    """Отображает следующую порцию объектов недвижимости"""
    user = update.effective_user
    redis_manager = RedisManager()
    
    # Рассчитываем конечный индекс
    end_index = start_index + Config.MAX_RESULTS_PER_PAGE
    if end_index > len(results):
        end_index = len(results)
    
    # Отправляем объекты
    for i in range(start_index, end_index):
        property_data = results[i]
        card = format_property_card(property_data, context.user_data)
        
        # Отправляем фото с описанием
        if card['photos']:
            await context.bot.send_photo(
                chat_id=user.id,
                photo=card['photos'][0],
                caption=card['text'],
                reply_markup=card['keyboard'],
                parse_mode="Markdown"
            )
        else:
            await context.bot.send_message(
                chat_id=user.id,
                text=card['text'],
                reply_markup=card['keyboard'],
                parse_mode="Markdown"
            )
    
    # Обновляем индекс в Redis
    redis_manager.set_search_index(user.id, end_index)
    
    # Проверяем, есть ли еще результаты
    has_more = end_index < len(results)
    
    # Отправляем навигационную клавиатуру
    await context.bot.send_message(
        chat_id=user.id,
        text="Выберите действие:",
        reply_markup=navigation_keyboard(has_more=has_more)
    )
    
    # Устанавливаем состояние просмотра результатов
    redis_manager.set_state(user.id, States.VIEWING_RESULTS)