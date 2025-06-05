# bot/data/repositories/search.py
# Репозиторий данных


import logging
from bot.core.database import DatabaseManager
from config import Config

logger = logging.getLogger(__name__)

def search_properties(criteria):
    """Поиск недвижимости по критериям в специфичной структуре таблиц"""
    all_results = []
    conn = None
    
    try:
        # Определяем какие таблицы нужно запрашивать
        tables = []
        room_type = criteria.get('rooms')
        
        if not room_type:
            logger.warning("Тип комнат не указан в критериях поиска")
            return []
        
        # Соответствие между выбором пользователя и типами в базе
        room_mapping = {
            'Студия': [1],
            '1': [2],
            '2': [3],
            '3': [4],
            '4+': [5, 6]
        }
        
        if room_type not in room_mapping:
            logger.warning(f"Неизвестный тип комнат: {room_type}")
            return []
        
        tables = room_mapping[room_type]
        conn = DatabaseManager.get_db_connection()
        
        for table_num in tables:
            table_name = f"`{table_num}`"
            cursor = conn.cursor(dictionary=True)
            
            try:
                # Базовый запрос
                query = f"""
                SELECT 
                    id, type, street, home, flat, price, pricem, space,
                    floor, floors_total, status, photo, photocnt, 
                    homeid, creation_date
                FROM {table_name}
                WHERE status = 1 
                """
                params = []
                
                # Фильтр по точной цене
                if 'price_exact' in criteria:
                    query += " AND price = %s"
                    params.append(int(criteria['price_exact']))
                else:
                    # Фильтр по диапазону цен
                    if 'price_min' in criteria:
                        query += " AND price >= %s"
                        params.append(int(criteria['price_min']))
                    
                    if 'price_max' in criteria:
                        query += " AND price <= %s"
                        params.append(int(criteria['price_max']))
                
                # Фильтр по этажу
                if 'floor' in criteria:
                    floor_filter = criteria['floor']
                    
                    if floor_filter == 'not_first':
                        query += " AND floor > 1"
                    elif floor_filter == 'not_last':
                        query += " AND floor < floors_total"
                    elif floor_filter == 'not_first_last':
                        query += " AND floor > 1 AND floor < floors_total"
                
                # Сортировка по дате создания
                query += " ORDER BY creation_date DESC"
                
                # Выполняем запрос
                cursor.execute(query, tuple(params))
                results = cursor.fetchall()
                
                # Преобразование дат в строки
                for result in results:
                    if 'creation_date' in result and result['creation_date']:
                        result['creation_date'] = result['creation_date'].strftime("%Y-%m-%d %H:%M:%S")
                
                # Добавляем тип комнат в результаты
                for result in results:
                    result['room_type'] = room_type
                    result['table_source'] = table_num
                
                all_results.extend(results)
                logger.info(f"Найдено {len(results)} объектов в таблице {table_num} для типа '{room_type}'")
                
            except Exception as e:
                logger.error(f"Ошибка при запросе к таблице {table_num}: {str(e)} {query}")
            finally:
                cursor.close()
    
    except Exception as e:
        logger.error(f"Общая ошибка при поиске: {str(e)}")
    finally:
        if conn:
            conn.close()
    
    return all_results