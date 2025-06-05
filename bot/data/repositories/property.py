# bot/data/repositories/property.py

import logging
from bot.core.database import DatabaseManager
from config import Config

logger = logging.getLogger(__name__)

def get_property_by_id(property_id, table_num=None):
    """
    Получение информации о недвижимости по ID
    :param table_num: номер таблицы (если известен)
    """
    conn = DatabaseManager.get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        if table_num:
            # Ищем в конкретной таблице
            cursor.execute(f"SELECT * FROM `{table_num}` WHERE id = %s", (property_id,))
            result = cursor.fetchone()
            if result:
                result['type'] = table_num
                
        else:
            # Поиск по всем таблицам
            for table_num in range(1, 7):
                cursor.execute(f"SELECT * FROM `{table_num}` WHERE id = %s", (property_id,))
                result = cursor.fetchone()
                if result:
                    result['type'] = table_num
                
        if result:
            # Добавляем тип объекта в результат
            result['object_type'] = table_num
            return result
    
        return None
    finally:
        cursor.close()
        conn.close()


 