# bot/data/repositories/favorites.py

import logging
from bot.core.database import DatabaseManager
from datetime import datetime

logger = logging.getLogger(__name__)

async def add_favorite_to_db(user_id, property_id):
    """Добавляет объект в избранное пользователя"""
    conn = None
    try:
        conn = DatabaseManager.get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO bot_favorites (user_id, property_id) VALUES (%s, %s)",
            (user_id, property_id)
        )
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Ошибка добавления в избранное: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()

async def remove_favorite_from_db(user_id, property_id):
    """Удаляет объект из избранного"""
    conn = None
    try:
        conn = DatabaseManager.get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM bot_favorites WHERE user_id = %s AND property_id = %s",
            (user_id, property_id)
        )
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Ошибка удаления из избранного: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()

async def is_favorite_in_db(user_id, property_id):
    """Проверяет, находится ли объект в избранном"""
    conn = None
    try:
        conn = DatabaseManager.get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM bot_favorites WHERE user_id = %s AND property_id = %s",
            (user_id, property_id)
        )
        return cursor.fetchone() is not None
    except Exception as e:
        logger.error(f"Ошибка проверки избранного: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()

async def get_user_favorites(user_id):
    """Возвращает список избранных объектов пользователя"""
    conn = None
    try:
        conn = DatabaseManager.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT property_id FROM bot_favorites WHERE user_id = %s",
            (user_id,)
        )
        return [row['property_id'] for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Ошибка получения избранного: {str(e)}")
        return []
    finally:
        if conn:
            conn.close()