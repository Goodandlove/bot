# bot/data/repositories/user.py

import logging
from bot.core.database import DatabaseManager
from bot.core.redis_manager import RedisManager
from bot.core.states import States

logger = logging.getLogger(__name__)

def get_agent_by_telegram_id(telegram_id):
    """Получает информацию об агенте по Telegram ID"""
    conn = DatabaseManager.get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute(
            "SELECT id, surename, firstname, secondname, telegram, status, role, types "
            "FROM agent WHERE telegram = %s LIMIT 1", 
            (telegram_id,)
        )
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()
 
def is_user_blocked(user_id):
    """Проверяет чёрный список с обработкой ошибок"""
    conn = None
    try:
        conn = DatabaseManager.get_db_connection()
        cursor = conn.cursor()
        
        # Проверка структуры таблицы
        cursor.execute("SHOW COLUMNS FROM blacklist_bot")
        columns = [col[0] for col in cursor.fetchall()]
        
        # Адаптивный запрос
        if 'active' in columns:
            query = "SELECT id FROM blacklist_bot WHERE telegram_uid = %s AND active = 1 LIMIT 1"
        else:
            query = "SELECT id FROM blacklist_bot WHERE telegram_uid = %s LIMIT 1"
        
        cursor.execute(query, (str(user_id),))
        result = cursor.fetchone()
        return bool(result)
        
    except Exception as e:
        logger.error(f"Ошибка проверки чёрного списка: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()

def log_new_connection(telegram_id, name):
    """Гарантированная запись в history_bot_try"""
    conn = None
    try:
        conn = DatabaseManager.get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO history_bot_try (telegram, name, created) VALUES (%s, %s, NOW())",
            (str(telegram_id), name))
        conn.commit()
        logger.info(f"Успешная запись в history_bot_try для {telegram_id}")
    except Exception as e:
        logger.error(f"Ошибка записи в history_bot_try: {str(e)}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

def log_user_session(telegram_id, name, level, message="Новая сессия"):
    """Гарантированная запись в history_bot_use"""
    conn = None
    try:
        conn = DatabaseManager.get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO history_bot_use 
            (telegram, name, message, session, created, level) 
            VALUES (%s, %s, %s, %s, NOW(), %s)""",
            (str(telegram_id), name, message, f"session_{telegram_id}", level))
        conn.commit()
        logger.info(f"Успешная запись в history_bot_use для {telegram_id}")
    except Exception as e:
        logger.error(f"Ошибка записи в history_bot_use: {str(e)}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

def log_user_action(telegram_id, name, action, level=0):
    """Логирует действие пользователя в history_bot_use"""
    conn = None
    try:
        conn = DatabaseManager.get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO history_bot_use 
            (telegram, name, message, session, created, level) 
            VALUES (%s, %s, %s, %s, NOW(), %s)""",
            (str(telegram_id), name, action, f"session_{telegram_id}", level))
        conn.commit()
    except Exception as e:
        logger.error(f"Ошибка записи действия: {str(e)}")
    finally:
        if conn:
            conn.close()

def log_search_query(user_id, name, criteria):
    """Логирование поискового запроса"""
    action = f"Поиск: {criteria}"
    log_user_action(user_id, name, action, level=1)


# Добавляем функцию получения избранного
def get_user_favorites(user_id):
    """Получает список избранных объектов пользователя"""
    conn = DatabaseManager.get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "SELECT property_id FROM user_favorites WHERE user_id = %s",
            (user_id,)
        )
        return [row[0] for row in cursor.fetchall()]
    finally:
        cursor.close()
        conn.close()