# bot/features/search/handlers.py
# Обработчики сообщений


import json
import asyncio
import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram import ReplyKeyboardRemove
from bot.features.search.services import SearchService
from bot.presentation.keyboards.search import (
    room_selection,
    price_selection,
    floor_selection,
    price_input_keyboard 
)
from bot.presentation.keyboards.common import pagination_keyboard

from bot.utils.input import parse_price_input
from bot.core.redis_manager import RedisManager
from bot.core.states import States
from bot.data.repositories.user import log_user_action
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

async def handle_price_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора типа ценового фильтра"""
    user = update.effective_user
    choice = update.message.text
    
    # Очищаем предыдущие значения цены
    RedisManager().conn.hdel(f'user:{user.id}:session', 'price_min')
    RedisManager().conn.hdel(f'user:{user.id}:session', 'price_max')
    
    # Проверяем, является ли выбор командой пропуска
    if choice == 'Пропустить':
        await update.message.reply_text(
            "🏢 *Этап 3: Этаж*\n\n"
            "Выберите предпочтения по этажу:",
            reply_markup=floor_selection(),
            parse_mode='Markdown'
        )
        RedisManager().set_state(user.id, States.SEARCH_FLOOR)
        return
    
    # Обработка выбора кнопок
    if choice == 'от - до':
        await update.message.reply_text(
            "💰 Введите цены в одном из форматов:\n"
            "- Одно число для точного значения (=цена)\n"
            "- Два числа через пробел/дефис для диапазона\n"
            "Примеры: *5000*, *=5000*, *5000-7500*, *5000 7500*",
            reply_markup=price_input_keyboard(),
            parse_mode='Markdown'
        )
        RedisManager().set_state(user.id, States.SEARCH_PRICE)
        return 
    
    if choice == 'цена от':
        await update.message.reply_text(
            "💸 Введите начальную цену поиска (например: 5000)",
            reply_markup=price_input_keyboard()
        )
        RedisManager().set_state(user.id, States.SEARCH_PRICE_MIN)
        return
    
    if choice == 'цена до':
        await update.message.reply_text(
            "💵 Введите максимальную цену поиска (например: 10000)",
            reply_markup=price_input_keyboard()
        )
        RedisManager().set_state(user.id, States.SEARCH_PRICE_MAX)
        return
    
    # Если получен неизвестный выбор
    await update.message.reply_text(
        "❌ Пожалуйста, выберите один из предложенных вариантов",
        reply_markup=price_selection()
    )

async def handle_price_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода цен"""
    user = update.effective_user
    message = update.message.text
    state = RedisManager().get_state(user.id)
    
    # Обработка команды "Пропустить"
    if message == "Пропустить":
        RedisManager().conn.hdel(f'user:{user.id}:session', 'price_min')
        RedisManager().conn.hdel(f'user:{user.id}:session', 'price_max')
        await update.message.reply_text(
            "🏢 *Этап 3: Этаж*\n\n"
            "Выберите предпочтения по этажу:",
            reply_markup=floor_selection(),
            parse_mode='Markdown'
        )
        RedisManager().set_state(user.id, States.SEARCH_FLOOR)
        return
    
    # Обработка команды "Назад"
    if message == "↩️ Назад":
        RedisManager().set_state(user.id, States.SEARCH_PRICE)
        await update.message.reply_text(
            "💰 Выберите тип фильтра по цене:",
            reply_markup=price_selection()
        )
        return
    
    # Определяем тип ввода
    input_type = "range"
    if state == States.SEARCH_PRICE_MIN:
        input_type = "min"
    elif state == States.SEARCH_PRICE_MAX:
        input_type = "max"
    
    # Парсим ввод
    prices = parse_price_input(message, input_type)
    
    # Обработка точного значения
    if prices["min"] is not None and prices["max"] is not None and prices["min"] == prices["max"]:
        response_text = f"✅ Точная цена установлена: {prices['min']} тыс. руб."
        RedisManager().set_search_data(user.id, 'price_exact', prices["min"])
    else:
        # Сохраняем результаты
        if prices["min"] is not None:
            RedisManager().set_search_data(user.id, 'price_min', prices["min"])
        if prices["max"] is not None:
            RedisManager().set_search_data(user.id, 'price_max', prices["max"])
        
        # Формируем ответ
        response_text = ""
        if state == States.SEARCH_PRICE_MIN and prices["min"] is not None:
            response_text = f"✅ Минимальная цена установлена: {prices['min']} тыс. руб."
        elif state == States.SEARCH_PRICE_MAX and prices["max"] is not None:
            response_text = f"✅ Максимальная цена установлена: {prices['max']} тыс. руб."
        elif state == States.SEARCH_PRICE:
            if prices["min"] is not None and prices["max"] is not None:
                response_text = f"✅ Ценовой диапазон установлен: {prices['min']}-{prices['max']} тыс. руб."
            elif prices["min"] is not None:
                response_text = f"✅ Минимальная цена установлена: {prices['min']} тыс. руб."
            elif prices["max"] is not None:
                response_text = f"✅ Максимальная цена установлена: {prices['max']} тыс. руб."
    
    # Если удалось распознать числа
    if response_text:
        response_text += "\n\n🏢 *Этап 3: Этаж*\nВыберите предпочтения по этажу:"
        await update.message.reply_text(
            response_text,
            reply_markup=floor_selection(),
            parse_mode='Markdown'
        )
        RedisManager().set_state(user.id, States.SEARCH_FLOOR)
    else:
        # Формируем сообщение об ошибке
        if state == States.SEARCH_PRICE_MIN:
            error_msg = "❌ Не удалось распознать минимальную цену. Введите число (например: 5000)"
        elif state == States.SEARCH_PRICE_MAX:
            error_msg = "❌ Не удалось распознать максимальную цену. Введите число (например: 10000)"
        else:
            error_msg = "❌ Не удалось распознать цены. Введите два числа (например: 5000 7500)"
        
        await update.message.reply_text(
            error_msg,
            reply_markup=price_input_keyboard()
        )

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