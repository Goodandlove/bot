# bot/presentation/keyboards/search.py


from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from bot.data.repositories.favorites import is_favorite_in_db
from bot.core.redis_manager import RedisManager
import asyncio

redis_manager = RedisManager()
    
def room_selection():
    return ReplyKeyboardMarkup([
        ['1', '2', '3'],
        ['↩️ Назад','4+', 'Студия']
    ], resize_keyboard=True)

def price_selection():
    return ReplyKeyboardMarkup([
        ['цена от', 'цена до', 'от - до'],
        ['↩️ Назад', 'Пропустить'] 
    ], resize_keyboard=True)

def floor_selection():
    return ReplyKeyboardMarkup([
        ['Не 1','Средний','Не последний'],        
        ['↩️ Назад', 'Показать']  
    ], resize_keyboard=True)

def price_input_keyboard():
    return ReplyKeyboardMarkup([
        ['↩️ Назад', 'Пропустить']
    ], resize_keyboard=True)

 
 
def details_keyboard(property_data, user_id=None):
    """Создаёт инлайн-клавиатуру с учётом состояния избранного"""
    property_id = property_data['id']
    photo_cnt = property_data.get('photocnt', 0)
    
    # Проверяем избранное через кеш Redis
    is_fav = redis_manager.is_favorite_in_cache(user_id, property_id) if user_id else False
    
    # Кнопка "Показать фото" с динамическим текстом
    buttons = []
    if photo_cnt > 0:
        photo_text = f"🖼 Показать {photo_cnt} фото"
        buttons.append(InlineKeyboardButton(photo_text, callback_data=f"details_{property_id}"))
    
    # Кнопка "В избранное" с изменяющейся иконкой
    fav_icon = "❤️" if is_fav else "🤍"
    fav_text = f"{fav_icon} В избранном" if is_fav else f"{fav_icon} В избранное"
    fav_button = InlineKeyboardButton(fav_text, callback_data=f"fav_{property_id}")
    
    # Формируем строки кнопок
    keyboard = []
    if buttons:
        keyboard.append(buttons)
    keyboard.append([fav_button])
    
    return InlineKeyboardMarkup(keyboard)

