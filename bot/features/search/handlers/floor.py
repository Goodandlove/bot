# bot\features\search\handlers\floor.py

import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram import ReplyKeyboardRemove
from bot.core.redis_manager import RedisManager
from bot.core.states import States
from bot.features.search.services import SearchService 
from bot.presentation.keyboards.common import pagination_keyboard, main_menu

logger = logging.getLogger(__name__)

async def handle_floor_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора фильтра по этажу"""
    user = update.effective_user
    floor_choice = update.message.text
    
    # Убираем клавиатуру выбора этажа
    await update.message.reply_text(
        "🔍 Ищу объекты по вашему запросу...",
        reply_markup=ReplyKeyboardRemove()
    )
    
    if floor_choice == 'Пропустить':
        # Очищаем выбор этажа
        RedisManager().conn.hdel(f'user:{user.id}:session', 'floor')
    
    # Получаем критерии поиска
    criteria = RedisManager().get_search_data_all(user.id)
    
    # Выполняем поиск
    results = await SearchService.perform_search(user, criteria)
    
    if not results:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="🔍 *Результаты поиска*\n\nПо вашему запросу ничего не найдено 😢\nПопробуйте изменить критерии поиска.",
            reply_markup=main_menu(),
            parse_mode='Markdown'
        )
    else:
        # Сохраняем результаты
        SearchService.save_search_results(user, results)
        
        # Показываем первую порцию
        pagination_info = await SearchService.show_results_batch(update, context, results, 0)
        
        # Показываем клавиатуру навигации
        if pagination_info["end_index"] < pagination_info["total_results"]:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Показано {pagination_info['end_index']} из {pagination_info['total_results']} объектов",
                reply_markup=pagination_keyboard(pagination_info['end_index'], pagination_info['total_results'])
            )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="🏠 Все объекты показаны. Возвращаемся в главное меню",
                reply_markup=main_menu()
            )
            RedisManager().set_state(user.id, States.MAIN_MENU)