# main.py

import asyncio
import logging
import sys
import os
import socket
from datetime import datetime

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler, 
    filters,
    ContextTypes,
)
from config import Config

from bot.core.middlewares import identify_user
from bot.features.common.handlers import (
    start,
    help_command,
    debug_session,
    check_blacklist
)
 

from bot.features.search.callbacks import register_callbacks as register_search_callbacks
from bot.features.message_router import route_message


# Класс для защиты от запуска нескольких экземпляров бота
class SingleInstance:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.bind(('localhost', 9999))
        except socket.error:
            raise RuntimeError("Бот уже запущен! Только один экземпляр может работать одновременно.")

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def wrap_handler(handler):
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            return await handler(update, context)
        except Exception as e:
            logger.error(f"Error in handler: {str(e)}", exc_info=True)
            raise
    return wrapped

async def setup_handlers(application: Application):
    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", wrap_handler(start)))
    application.add_handler(CommandHandler("help", wrap_handler(help_command)))
    application.add_handler(CommandHandler("debug", wrap_handler(debug_session)))
    application.add_handler(CommandHandler("check_block", wrap_handler(check_blacklist)))
    
    # Обработчики сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, wrap_handler(route_message)))
    
    # Регистрируем callback-обработчики
    register_search_callbacks(application)

async def main():
    # Проверка на уникальность экземпляра
    try:
        SingleInstance()
    except RuntimeError as e:
        logger.error(str(e))
        sys.exit(1)

    application = None
    try:
        application = Application.builder().token(Config.BOT_TOKEN).build()
        await setup_handlers(application)
        
        logger.info("Бот запущен и готов к работе")
        await application.initialize()
        await application.start()
        await application.updater.start_polling(drop_pending_updates=True)
        
        # Бесконечный цикл до ручной остановки
        while True:
            await asyncio.sleep(3600)
            
    except Exception as e:
        logger.error(f"Ошибка в основном цикле: {str(e)}", exc_info=True)
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки")
    finally:
        if application:
            try:
                await application.stop()
                await application.shutdown()
                logger.info("Бот корректно остановлен")
            except Exception as e:
                logger.error(f"Ошибка при остановке: {str(e)}")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Фатальная ошибка: {str(e)}", exc_info=True)
        sys.exit(1)