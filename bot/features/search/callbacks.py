# bot/features/search/callbacks.py
# Обработчики callback


import json
import logging
import asyncio
from telegram import Update
from config import Config

from bot.core.redis_manager import RedisManager

from bot.features.search.services import SearchService
from bot.core.states import States
from bot.presentation.keyboards.common import main_menu
from bot.presentation.keyboards.common import pagination_keyboard
from bot.presentation.keyboards.search import details_keyboard
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    ContextTypes,
)
from bot.data.repositories.favorites import is_favorite_in_db,remove_favorite_from_db,add_favorite_to_db
from bot.data.repositories.property import get_property_by_id
from bot.presentation.keyboards.search import room_selection
from bot.presentation.cards.search import get_all_photos, format_property_card
from bot.data.repositories.property import get_property_by_id

logger = logging.getLogger(__name__)
redis_manager = RedisManager()

async def handle_show_more(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    # Получаем сохраненные результаты
    results_json = redis_manager.get_search_data(user.id, 'search_results')
    current_index = int(redis_manager.get_search_data(user.id, 'search_index') or 0)
    
    if not results_json:
        await query.message.reply_text("Результаты поиска устарели. Пожалуйста, выполните новый поиск.")
        return
    
    results = json.loads(results_json)
    
    # Удаляем сообщение с кнопкой
    await query.message.delete()
    
    # Показываем следующую порцию
    pagination_info = await SearchService.show_results_batch(update, context, results, current_index)
    
    # Обновляем клавиатуру пагинации
    if pagination_info["end_index"] < pagination_info["total_results"]:
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=f"Показано {pagination_info['end_index']} из {pagination_info['total_results']} объектов",
            reply_markup=pagination_keyboard(pagination_info['end_index'], pagination_info['total_results'])
        )
    else:
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="🏠 Все объекты показаны. Возвращаемся в главное меню",
            reply_markup=main_menu()
        )
        redis_manager.set_state(user.id, States.MAIN_MENU)

async def handle_back_to_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    # Получаем сохраненные результаты
    results_json = redis_manager.get_search_data(user.id, 'search_results')
    current_index = int(redis_manager.get_search_data(user.id, 'search_index') or 0)
    
    if not results_json:
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="🔍 Результаты поиска устарели. Выполните новый поиск."
        )
        return
    
    results = json.loads(results_json)
    
    # Удаляем сообщение с кнопкой
    await query.message.delete()
    
    # Показываем следующую порцию
    await SearchService.show_results_batch(update, context, results, current_index)

def register_callbacks(application: Application):
    """Регистрирует все callback-обработчики для поиска"""
    application.add_handler(CallbackQueryHandler(handle_show_more, pattern="^show_more$"))
    application.add_handler(CallbackQueryHandler(handle_back_to_search, pattern="^back_to_search$"))



async def handle_show_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка кнопки 'Показать фото'"""

    
    query = update.callback_query
    await query.answer()
    property_id = query.data.split('_')[1]
    
    # Получаем данные объекта
    property_data = await asyncio.to_thread(
        get_property_by_id, 
        property_id
    )
    
    if not property_data:
        await query.message.reply_text("⚠️ Объект не найден в базе данных")
        return
    
    # Получаем все фото
    all_photos = get_all_photos(property_data)
    chat_id = query.message.chat_id
    
    # Отправляем сообщение о начале показа
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"🖼 Загружаю {len(all_photos)} фото для объекта {property_id}..."
    )
    
    # Отправляем фото по одному (можно альбомом, но так надежнее)
    for photo_url in all_photos:
        try:
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=photo_url
            )
        except Exception as e:
            logger.error(f"Ошибка отправки фото {photo_url}: {str(e)}")
    
    # Отправляем финальное сообщение с карточкой объекта
    card = format_property_card(property_data, context.user_data, detailed=True)
    
    # Формируем номер объявления
    ad_number = f"{property_data['id']}{Config.CITY_CODE}{property_data['type']}"
    
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"🏁 Все фото для объекта `{ad_number}` показаны\n\n{card['text']}",
        reply_markup=card['keyboard'],
        parse_mode='Markdown'
    )


async def handle_add_favorite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка кнопки 'В избранное' с переключением состояния"""
    query = update.callback_query
    await query.answer()
    property_id = query.data.split('_')[1]
    user = query.from_user
    
    # Загружаем данные объекта из БД
    property_data = await asyncio.to_thread(get_property_by_id, property_id)
    
    if not property_data:
        await query.message.reply_text("⚠️ Объект не найден в базе данных")
        return
    
    # Переключаем состояние в базе данных
    if await is_favorite_in_db(user.id, property_id):
        await remove_favorite_from_db(user.id, property_id)
        action = "удален из"
        icon = "🤍"
    else:
        await add_favorite_to_db(user.id, property_id)
        action = "добавлен в"
        icon = "❤️"
    
    # Удаляем старое сообщение с карточкой
    try:
        await query.message.delete()
    except Exception as e:
        logger.error(f"Ошибка удаления сообщения: {str(e)}")
    
    # Отправляем уведомление
    await context.bot.send_message(
        chat_id=user.id,
        text=f"{icon} Объект {property_id} {action} избранное!"
    )
    
    # Отправляем ОБНОВЛЕННУЮ карточку объекта
    card = format_property_card(property_data, context.user_data)
    new_keyboard = details_keyboard(property_data, user.id)
    
    try:
        if card['photos']:
            await context.bot.send_photo(
                chat_id=user.id,
                photo=card['photos'][0],
                caption=card['text'],
                reply_markup=new_keyboard,
                parse_mode='Markdown'
            )
        else:
            await context.bot.send_message(
                chat_id=user.id,
                text=card['text'],
                reply_markup=new_keyboard,
                parse_mode='Markdown'
            )
    except Exception as e:
        logger.error(f"Ошибка отправки обновленной карточки: {str(e)}")
 
# bot/features/search/callbacks.py (добавляем обработчики)

async def handle_new_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка кнопки 'Новый поиск'"""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    
    # Очищаем данные поиска
    RedisManager().conn.hdel(f'user:{user.id}:session', 'search_results')
    RedisManager().conn.hdel(f'user:{user.id}:session', 'search_index')
    
    # Устанавливаем начальное состояние
    RedisManager().set_state(user.id, States.SEARCH_ROOMS.value)
    
    # Отправляем сообщение для начала нового поиска
    
    await query.message.reply_text(
        "🔄 Начинаем новый поиск! Выберите количество комнат:",
        reply_markup=room_selection()
    )

# Обновляем register_callbacks
def register_callbacks(application: Application):
    application.add_handler(CallbackQueryHandler(handle_show_more, pattern="^show_more$"))
    application.add_handler(CallbackQueryHandler(handle_back_to_search, pattern="^back_to_search$"))
    application.add_handler(CallbackQueryHandler(handle_show_details, pattern=r"^details_"))
    application.add_handler(CallbackQueryHandler(handle_add_favorite, pattern=r"^fav_"))
    application.add_handler(CallbackQueryHandler(handle_new_search, pattern="^new_search$"))  # Новый обработчик

    application.add_handler(CallbackQueryHandler(
        new_search_callback, 
        pattern="^new_search$"
    ))
    
    application.add_handler(CallbackQueryHandler(
        show_more_callback, 
        pattern="^show_more$"
    ))

# Обработчик для кнопки "Новый поиск" 
async def new_search_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    redis_manager = RedisManager()
    
    # Очищаем данные поиска
    redis_manager.clear_search_session(user_id)
    
    # Устанавливаем начальное состояние
    redis_manager.set_state(user_id, States.SEARCH_ROOMS)
    
    # Отправляем сообщение с началом нового поиска
    await query.message.reply_text(
        "🔍 Выберите количество комнат:",
        reply_markup=room_selection()
    )

async def show_more_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    redis_manager = RedisManager()
    
    # Получаем текущий индекс и результаты
    current_index = redis_manager.get_search_index(user_id)
    results = redis_manager.get_search_results(user_id)
    
    # Показываем следующие объекты
    # await show_next_properties(update, context, current_index, results)


# Обновленный обработчик избранного, формирование сообщений:
async def favorite_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    property_id = int(query.data.split('_')[1])
    redis_manager = RedisManager()
    
    # Определяем текущее состояние
    is_favorite = redis_manager.is_favorite_in_cache(user_id, property_id)
    
    # Формируем полный номер объекта
    property_data = get_property_by_id(property_id)
    if property_data:
        ad_number = f"{property_id}{Config.CITY_CODE}{property_data['type']}"
        

    if is_favorite:
        # Удаляем из избранного
        success = redis_manager.remove_favorite(user_id, property_id)
        if success:
            redis_manager.remove_favorite_from_cache(user_id, property_id)
            # await query.answer("🤍 Объект удален из избранного!")
            await query.answer(f"🤍 Объект {ad_number} удален из избранного!")
        else:
            await query.answer("❌ Ошибка при удалении {ad_number} из избранного")

 
    else:
        # Добавляем в избранное
        success = redis_manager.add_favorite(user_id, property_id)
        if success:
            redis_manager.add_favorite_to_cache(user_id, property_id)
            # await query.answer("❤️ Объект добавлен в избранное!")
            await query.answer(f"❤️ Объект {ad_number} добавлен в избранное!")
        else:
            await query.answer("❌ Ошибка при добавлении {ad_number} в избранное")
    


    # Переотправляем карточку с обновленной кнопкой
    property_data = get_property_by_id(property_id)
    if property_data:
        card = format_property_card(property_data, context.user_data)
        try:
            await query.message.edit_reply_markup(reply_markup=card["keyboard"])
        except:
            # Если не удалось изменить сообщение, отправляем новое
            await query.message.reply_photo(
                photo=card["photos"][0] if card["photos"] else None,
                caption=card["text"],
                reply_markup=card["keyboard"],
                parse_mode="Markdown"
            )