# bot\core\redis_manager.py


import json
import redis
from config import Config
from bot.core.states import States

class RedisManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.connection = Config.get_redis_connection()
        return cls._instance
    
    @property
    def conn(self):
        return self.connection
    
    def set_state(self, user_id, state):
        state_value = state.value if hasattr(state, 'value') else state
        self.connection.set(f'user:{user_id}:state', state_value)
  
    def get_state(self, user_id):
        state = self.connection.get(f'user:{user_id}:state')
        # Возвращаем значение как экземпляр States, если возможно
        return States(int(state)) if state else States.MAIN_MENU
    
    def set_search_data(self, user_id, key, value):
        self.connection.hset(f'user:{user_id}:session', key, value)
    
    def get_search_data(self, user_id, key):
        value = self.connection.hget(f'user:{user_id}:session', key)
        return value.decode() if value else None
    
    def get_search_data_all(self, user_id):
        data = self.connection.hgetall(f'user:{user_id}:session')
        return {k.decode(): v.decode() for k, v in data.items()} if data else {}
    
    def clear_session(self, user_id):
        """Полная очистка сессии пользователя"""
        self.connection.delete(f'user:{user_id}:session')
        self.connection.delete(f'user:{user_id}:state')
    
    
    

    def add_favorite(self, user_id, property_id):
        """Добавляет объект в избранное пользователя"""
        self.connection.sadd(f'user:{user_id}:favorites', property_id)
    
    def remove_favorite(self, user_id, property_id):
        """Удаляет объект из избранного"""
        self.connection.srem(f'user:{user_id}:favorites', property_id)
    
    def get_favorites(self, user_id):
        """Возвращает список избранных объектов"""
        return [pid.decode() for pid in self.connection.smembers(f'user:{user_id}:favorites')]
    
    def is_favorite(self, user_id, property_id):
        """Проверяет, находится ли объект в избранном"""
        return self.connection.sismember(f'user:{user_id}:favorites', property_id)
    
    
 
    def add_favorite_to_cache(self, user_id, property_id):
        """Добавляет объект в кэш избранного"""
        self.connection.sadd(f'user:{user_id}:favorites_cache', property_id)
    
    def remove_favorite_from_cache(self, user_id, property_id):
        """Удаляет объект из кэша избранного"""
        self.connection.srem(f'user:{user_id}:favorites_cache', property_id)
    
    def is_favorite_in_cache(self, user_id, property_id):
        """Проверяет наличие объекта в кэше избранного"""
        return self.connection.sismember(f'user:{user_id}:favorites_cache', property_id)
    
    def refresh_favorites_cache(self, user_id, favorites):
        """Обновляет весь кэш избранного"""
        key = f'user:{user_id}:favorites_cache'
        self.connection.delete(key)
        for prop_id in favorites:
            self.connection.sadd(key, prop_id)



     

    def set_search_results(self, user_id, results):
        """Сохраняет результаты поиска в Redis"""
        results_json = json.dumps(results)
        self.connection.hset(f'user:{user_id}:session', 'search_results', results_json)
    
    def get_search_results(self, user_id):
        """Получает результаты поиска из Redis"""
        results_json = self.connection.hget(f'user:{user_id}:session', 'search_results')
        return json.loads(results_json) if results_json else []
    
    def set_search_index(self, user_id, index):
        """Устанавливает текущий индекс поиска"""
        self.connection.hset(f'user:{user_id}:session', 'search_index', index)
    
    def get_search_index(self, user_id):
        """Получает текущий индекс поиска"""
        index = self.connection.hget(f'user:{user_id}:session', 'search_index')
        return int(index) if index else 0
    
    def clear_search_session(self, user_id):
        """Очищает данные поиска, сохраняя избранное"""
        self.connection.hdel(f'user:{user_id}:session', 'search_results', 'search_index')
        self.connection.delete(f'user:{user_id}:state')
 
    