# bot\core\database.py

import mysql.connector
import redis
from config import Config

class DatabaseManager:
    @staticmethod
    def get_db_connection():
        return mysql.connector.connect(**Config.DB_CONFIG)
    
    @staticmethod
    def get_redis_connection():
        return redis.Redis.from_url(Config.REDIS_URL)