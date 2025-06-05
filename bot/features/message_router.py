# bot/features/message_router.py

import logging
import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from bot.core.middlewares import identify_user
from bot.features.common.handlers import handle_global_commands
from bot.features.search.handlers.results import show_next_properties
from bot.features.search.handlers import (
    handle_room_selection,
    handle_price_selection,
    handle_price_input,
    handle_floor_selection
)
from bot.core.states import States
from bot.core.redis_manager import RedisManager
from bot.features.common.handlers import start  # Импорт функции start

from bot.presentation.keyboards.search import room_selection, price_selection


logger = logging.getLogger(__name__)

async def route_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return
    
    if await identify_user(update, context):
        return

    user = update.effective_user
    message = update.message.text
    state = RedisManager().get_state(user.id)

    # Логируем состояние и сообщение
    logger.info(f"Обработка сообщения: состояние={state}, текст='{message}'")

    # Обработка глобальных команд
    if await handle_global_commands(update, context):
        return
    
    # Обработка навигационных кнопок
    if message == "🔍 Показать еще":
        redis_manager = RedisManager()
        current_index = redis_manager.get_search_index(user.id)
        results = redis_manager.get_search_results(user.id)
        
        if current_index < len(results):
            await show_next_properties(update, context, current_index, results)
        else:
            await update.message.reply_text("Больше результатов нет.")
        return
    
    elif message == "🔄 Новый поиск":
        redis_manager = RedisManager()
        redis_manager.clear_search_session(user.id)
        redis_manager.set_state(user.id, States.SEARCH_ROOMS)
        await update.message.reply_text(
            "🔍 Выберите количество комнат:",
            reply_markup=room_selection()
        )
        return
    
    # Обработка состояний поиска
    if state == States.SEARCH_ROOMS:
        if message == "↩️ Назад":
            await start(update, context)  # Используем импортированную функцию start
            RedisManager().set_state(user.id, States.MAIN_MENU)
        else:
            await handle_room_selection(update, context)
        return
    
    elif state == States.SEARCH_PRICE:
        # Обработка кнопки "Назад"
        if message == "↩️ Назад":
            RedisManager().set_state(user.id, States.SEARCH_ROOMS)
            await update.message.reply_text(
                "🔍 Выберите количество комнат:",
                reply_markup=room_selection()
            )
            return
        
        # Передаем обработку в специализированный обработчик
        await handle_price_selection(update, context)
        return
    
    elif state in [States.SEARCH_PRICE_MIN, States.SEARCH_PRICE_MAX, States.SEARCH_PRICE]:
        await handle_price_input(update, context)
        return
    
    elif state == States.SEARCH_FLOOR:
        if message == "↩️ Назад":
            RedisManager().set_state(user.id, States.SEARCH_PRICE)
            await update.message.reply_text(
                "💰 Выберите тип фильтра по цене:",
                reply_markup=price_selection()
            )
        else:
            await handle_floor_selection(update, context)
        return
    
    # Если ни одно из условий не сработало
    if context.user_data.get('type') == 'agent':
        await update.message.reply_text(f"Сообщение агенту: {message}")
    else:
        await update.message.reply_text(f"Сообщение пользователю: {message}")