# config.py

import os
import redis
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    
    # MySQL конфигурация
    DB_CONFIG = {
        'host': os.getenv('DB_HOST'),
        'port': int(os.getenv('DB_PORT', 3306)),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'database': os.getenv('DB_NAME')
    }
    
  
    # Redis конфигурация
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # Флаг разработки
    DEV_MODE = True
    
    # Базовый URL для фотографий
    PHOTO_BASE_URL = "http://kvartiri-v-gelendzhike.ru/gelendzhik/"
    
    # Максимальное количество объектов за один запрос
    MAX_RESULTS_PER_PAGE = 5

    # Код города для формирования номеров объектов
    CITY_CODE = '02'
    
    @staticmethod
    def get_redis_connection():
        """Создает соединение с Redis"""
        return redis.Redis.from_url(Config.REDIS_URL)
    
    @staticmethod
    def get_db_connection():
        """Создает соединение с MySQL"""
        return mysql.connector.connect(
            host=Config.DB_CONFIG['host'],
            port=Config.DB_CONFIG['port'],
            user=Config.DB_CONFIG['user'],
            password=Config.DB_CONFIG['password'],
            database=Config.DB_CONFIG['database']
        )

# Тест соединений
if __name__ == "__main__":
    print("Проверка конфигурации...")
    
    # Проверка Redis
    try:
        redis_conn = Config.get_redis_connection()
        redis_conn.ping()
        print("✅ Redis: соединение успешно")
    except Exception as e:
        print(f"❌ Redis ошибка: {str(e)}")
    
    # Проверка MySQL
    try:
        db_conn = Config.get_db_connection()
        cursor = db_conn.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()[0]
        print(f"✅ MySQL: версия сервера {version}")
        cursor.close()
        db_conn.close()
    except Exception as e:
        print(f"❌ MySQL ошибка: {str(e)}")