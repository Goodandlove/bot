# bot/features/common/handlers.py

import logging
from telegram import Update
from telegram.ext import ContextTypes
from bot.core.redis_manager import RedisManager
from bot.core.states import States
from bot.presentation.keyboards.common import main_menu, help_menu
from bot.features.cabinet.handlers import show_favorites
from bot.features.cabinet.handlers import show_cabinet, show_favorites 

import asyncio
from bot.core.redis_manager import RedisManager
from bot.data.repositories.user import is_user_blocked, get_agent_by_telegram_id

logger = logging.getLogger(__name__)
redis_manager = RedisManager() 


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    
    # Приветствие
    if context.user_data.get('is_agent'):
        welcome = f"Добро пожаловать, {context.user_data['agent_name']}!"
    else:
        welcome = "Добро пожаловать!"
    
    # Основной текст приветствия
    welcome_text = (
        "🏖 *Добро пожаловать в бот по поиску недвижимости в Геленджике!*\n\n"
        "Здесь вы можете:\n"
        "- 🔍 Искать квартиры по параметрам\n"
        "- ❤ Сохранять в избранное\n"
        "- 💼 Размещать заявки на подбор\n\n"
        "- 📢 Размещать свои объявления\n\n"
        "- 🔄 Создавать подписки на уведомления\n\n"
        "Используйте меню или команды для навигации!\n"
        "Начните с /search для поиска недвижимости."
    )
    
    await update.message.reply_text(welcome)
    await update.message.reply_text(welcome_text, reply_markup=main_menu(), parse_mode='Markdown')
    RedisManager().set_state(user.id, States.MAIN_MENU)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🏖 *Помощь по использованию бота*\n\n"
        "🔍 *Поиск недвижимости:*\n"
        "- Используйте /search для начала поиска\n"
        "- Пошагово укажите параметры: комнаты, цена, этаж\n\n"
        "🆕 *Новые объекты:*\n"
        "- /new - новые предложения за последние 24 часа или 3 дня\n\n"

        "⭐ *Избранное:*\n"
        "- Сохраняйте понравившиеся объекты кнопкой '❤ Избранное'\n"
        "- Просматривайте сохраненное через /favorites\n\n"        
        "💼 *Мой кабинет:*\n"
        "- Размещайте ваши объекты\n\n"
        "- Размещайте ваши запросы на подборку объектов\n\n"        
        "- Отслеживайте статус ваших запросов через /requests\n\n"
        "⚙ *Настройки:*\n"
        "- /settings - управление уведомлениями\n\n"        
        "🔄 /reset - сбросить текущий поиск\n"
        "🏠 /start - перезапустить бота"
    )
    await update.message.reply_text(help_text, reply_markup=help_menu(), parse_mode='Markdown')
    RedisManager().set_state(update.effective_user.id, States.HELP_MENU)

 

async def handle_global_commands(update: Update, context: ContextTypes.DEFAULT_TYPE): 
    user = update.effective_user
    message = update.message.text

    if message == "❤ Избранное":
        await show_favorites(update, context)
        return True
    
    if message == "💼 Мой кабинет":
        await show_cabinet(update, context)
        return True
    
    if message == "ℹ Помощь":
        await help_command(update, context)
        RedisManager().set_state(user.id, States.HELP_MENU)
        return True
    
    if message == "🏠 Главная":
        await start(update, context)
        RedisManager().set_state(user.id, States.MAIN_MENU)
        return True
    
    if message == "🔍 Поиск":
        from bot.features.search.handlers.start import start_search
        await start_search(update, context)
        return True
    
    return False



async def debug_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Временная команда для отладки"""
    user = update.effective_user
    if not user:
        return
    
    # Получаем все данные сессии
    session_data = redis_manager.get_search_data_all(user.id)
    db_data = {
        'is_blocked': await asyncio.to_thread(is_user_blocked, user.id),
        'agent_info': await asyncio.to_thread(get_agent_by_telegram_id, user.id)
    }
    
    text = (
        f"🛠 *Debug информация*\n\n"
        f"ID: `{user.id}`\n"
        f"Redis данные:\n`{session_data}`\n\n"
        f"DB статус:\n`{db_data}`"
    )
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def check_blacklist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Временная команда для проверки чёрного списка"""
    user = update.effective_user
    if not user:
        await update.message.reply_text("Пользователь не идентифицирован")
        return
    
    is_blocked = await asyncio.to_thread(is_user_blocked, user.id)
    status = "заблокирован" if is_blocked else "не заблокирован"
    
    await update.message.reply_text(
        f"Статус блокировки для {user.full_name} (ID: {user.id}): {status}"
    ) 