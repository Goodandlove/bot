# bot/features/search/services.py
# Сервисный слой (бизнес-логика)



import json
import asyncio
import logging
from bot.core.redis_manager import RedisManager
from bot.data.repositories.search import search_properties
from bot.presentation.cards.search import format_property_card
from bot.core.states import States
from config import Config

redis_manager = RedisManager() 

logger = logging.getLogger(__name__)
BATCH_SIZE = Config.MAX_RESULTS_PER_PAGE

class SearchService:
    @staticmethod
    async def start_search(user):
        """Инициализация процесса поиска"""
        try:
            redis_manager.clear_session(user.id)
            redis_manager.set_state(user.id, States.SEARCH_ROOMS.value)
            logger.info(f"Начало поиска для пользователя {user.id}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при начале поиска: {str(e)}")
            return False

    @staticmethod
    async def perform_search(user, criteria):
        """Выполнение поиска по критериям"""
        # Формируем читаемый критерий для логов
        log_criteria = ", ".join([f"{k}: {v}" for k, v in criteria.items()])
        
        # Выполняем поиск в БД
        return await asyncio.to_thread(search_properties, criteria)

    @staticmethod
    def save_search_results(user, results):
        """Сохранение результатов поиска в Redis"""
        redis_manager.set_search_data(user.id, 'search_results', json.dumps(results))
        redis_manager.set_search_data(user.id, 'search_index', 0)

    @staticmethod
    async def show_results_batch(update, context, results, start_index):
        """Показывает порцию результатов"""
        user = update.effective_user
        end_index = min(start_index + BATCH_SIZE, len(results))
        batch = results[start_index:end_index]
        
        # Определяем chat_id
        chat_id = update.effective_chat.id
        
        # Сообщение с информацией о результатах
        total = len(results)
        shown = end_index
        
        if start_index == 0:
            message_text = (
                f"🏆 *Результаты поиска*\n\n"
                f"Найдено объектов: *{total}*\n"
                f"Показано: *{shown}*"
            )
            await context.bot.send_message(
                chat_id=chat_id,
                text=message_text,
                parse_mode='Markdown'
            )
         
        # Отправляем карточки объектов
        for prop in batch:
            # Сохраняем тип объекта в контексте
            context.user_data['current_property_type'] = prop['type'] 
            card = format_property_card(prop, context.user_data)
            
            if card['photos']:
                try:
                    await context.bot.send_photo(
                        chat_id=chat_id,
                        photo=card['photos'][0],
                        caption=card['text'],
                        reply_markup=card['keyboard'],
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    logger.error(f"Ошибка при отправке фото: {str(e)}")
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=f"{card['text']}\n\n⚠️ Фото недоступно",
                        reply_markup=card['keyboard'],
                        parse_mode='Markdown'
                    )
            else:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=card['text'],
                    reply_markup=card['keyboard'],
                    parse_mode='Markdown'
                )
        
        # Обновляем индекс в Redis
        redis_manager.set_search_data(user.id, 'search_index', end_index)
        
        # Возвращаем информацию о пагинации
        return {
            "end_index": end_index,
            "total_results": len(results)
        }