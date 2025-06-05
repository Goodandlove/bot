# bot\core\middlewares.py

import asyncio
import logging
from bot.core.database import DatabaseManager
from bot.data.repositories.user import (
    get_agent_by_telegram_id, 
    log_new_connection, 
    log_user_session, 
    is_user_blocked
)
from bot.core.redis_manager import RedisManager
from bot.core.states import States
from telegram import Update
from telegram.ext import ContextTypes
from bot.data.repositories.favorites import get_user_favorites


logger = logging.getLogger(__name__)
redis_manager = RedisManager()

async def identify_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return False

    # 1. Проверяем наличие сессии
    session_data = redis_manager.get_search_data_all(user.id)
    has_session = bool(session_data)
    
    # 2. Проверяем блокировку
    is_blocked = False
    try:
        is_blocked = await asyncio.to_thread(is_user_blocked, user.id)
    except Exception as e:
        logger.error(f"Ошибка проверки блокировки: {str(e)}")
    

    # 3. Логирование по условиям
    try:
        if is_blocked:
            # Условие 1: Пользователь в блоке
            await asyncio.to_thread(
                log_new_connection, 
                user.id, 
                user.full_name
            )
            await update.message.reply_text("⛔ Ваш аккаунт заблокирован")
            return True
            
        elif not has_session:
            # Условие 2: Нет сессии и не в блоке
            await asyncio.to_thread(
                log_new_connection, 
                user.id, 
                user.full_name
            )
            
            # Загружаем избранное из БД в кеш Redis
            try:
                favorites = await asyncio.to_thread(get_user_favorites, user.id)
                if favorites:
                    redis_manager.refresh_favorites_cache(user.id, favorites)
            except Exception as e:
                logger.error(f"Ошибка загрузки избранного: {str(e)}")

            # Создаем новую сессию
            agent_info = await asyncio.to_thread(get_agent_by_telegram_id, user.id)
            if agent_info and agent_info['status'] == 1:
                session_data = {
                    'type': 'agent',
                    'status': agent_info['status'],
                    'role': agent_info['role'],
                    'types': agent_info['types'],
                    'name': f"{agent_info['surename']} {agent_info['firstname']}"
                }
                level = 1
            else:
                session_data = {
                    'type': 'user',
                    'status': 'active',
                    'role': 0,
                    'name': user.full_name
                }
                level = 0
            
            for key, value in session_data.items():
                redis_manager.set_search_data(user.id, key, value)
            
            await asyncio.to_thread(
                log_user_session, 
                user.id, 
                session_data['name'], 
                level,
                "Новая сессия"
            )
            context.user_data.update(session_data)
            
    except Exception as e:
        logger.error(f"Ошибка логирования: {str(e)}")
    
    
    # 4. Для существующих сессий
    if has_session and not is_blocked:
        # Обновляем контекст
        context.user_data.update(session_data)
        
        # Логируем действие в history_bot_use
        action = ""
        if update.message:
            action = update.message.text
        elif update.callback_query:
            action = update.callback_query.data
            
        await asyncio.to_thread(
            log_user_session, 
            user.id, 
            session_data.get('name', user.full_name), 
            session_data.get('level', 0),
            action
        )
    
    return False