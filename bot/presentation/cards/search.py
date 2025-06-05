# bot/presentation/cards/search.py
# Представление (карточки)

from bot.presentation.keyboards.search import details_keyboard

import logging
from bot.core.utils import format_price, format_date
from config import Config
from bot.core.utils import format_object_number

logger = logging.getLogger(__name__)

FLAT_TYPES = {
    "1": "Студия",
    "2": "Однокомнатная",
    "3": "Двухкомнатная",
    "4": "Трехкомнатная",
    "5": "Четырехкомнатная",
    "6": "Многокомнатная"
}

PATH_PREFIXES = {
    "1": "studiya",
    "2": "odnokomnatnaya_kvartira",
    "3": "dvuchkomnatnaya_kvartira",
    "4": "trechkomnatnaya_kvartira",
    "5": "chetirechkomnatnaya_kvartira",
    "6": "mnogokomnatnaya_kvartira"
}

def get_photo_path(prop_id, prop_type, photo_num=0):
    """Генерирует путь к фото объекта"""
    prefix = PATH_PREFIXES.get(str(prop_type), "")
    if not prefix:
        return None
        
    # Формируем путь к изображению
    path = f"{prefix}_v_gelendzhike/{prop_id}{Config.CITY_CODE}{prop_type}/"
    
    # Определяем имя файла
    if photo_num == 0:
        filename = f"{prop_id}{Config.CITY_CODE}{prop_type}_sq.jpg"
    else:
        filename = f"{prop_id}{Config.CITY_CODE}{prop_type}_{photo_num}.jpg"
    
    return f"{Config.PHOTO_BASE_URL}{path}{filename}"
 
def get_additional_photos(property_data):
    """Возвращает список дополнительных фото (исключая превью)"""
    prop_id = property_data['id']
    prop_type = property_data['type']
    photos = []
    photo_cnt = property_data.get('photocnt', 0)
    
    # Если нет поля 'photo' или оно пустое
    if 'photo' not in property_data or not property_data['photo']:
        # Генерируем номера фото от 1 до photocnt
        for num in range(1, photo_cnt):
            photo_url = get_photo_path(prop_id, prop_type, num)
            if photo_url:
                photos.append(photo_url)
        return photos
    
    # Парсим номера фото из строки
    try:
        # Преобразуем "0,1,2,4" в список [1,2,4] (исключая 0)
        photo_numbers = [
            int(num.strip()) 
            for num in property_data['photo'].split(',') 
            if num.strip() and int(num.strip()) != 0
        ]
        
        # Формируем URL для каждого номера
        for num in photo_numbers:
            photo_url = get_photo_path(prop_id, prop_type, num)
            if photo_url:
                photos.append(photo_url)
                
    except Exception as e:
        logger.error(f"Ошибка парсинга номеров фото: {str(e)}")
        # Генерируем по photocnt
        for num in range(1, photo_cnt):
            photo_url = get_photo_path(prop_id, prop_type, num)
            if photo_url:
                photos.append(photo_url)
    
    return photos

def format_property_card(property_data, user_info, detailed=False):
    """Форматирует карточку объекта недвижимости"""
    prop_id = property_data.get('id')
    prop_type = property_data.get('type')
    
    # Формируем номер объявления: используем prop_type вместо room_count 
    ad_number = format_object_number(property_data['id'], property_data['type'])

    # Базовые данные
    flat_type = FLAT_TYPES.get(str(prop_type), "Квартира")
    street = property_data.get('street', '')
    home = property_data.get('home', '')
    flat = property_data.get('flat', '')
    price = property_data.get('price', 0)
    pricem = property_data.get('pricem', 0)
    space = property_data.get('space', 0)
    floor = property_data.get('floor', 0)
    floors_total = property_data.get('floors_total', 0)
    photo_cnt = property_data.get('photocnt', 0)
    created = format_date(property_data.get('creation_date', ''))
    
    # Форматирование адреса
    address = f"{street}, д. {home}"
    if flat:
        address += f", кв. {flat}"
    
    # Определяем уровень доступа
    is_agent = user_info.get('type') == 'agent'
    has_access = False
    
    if is_agent:
        # Проверяем доступ к типу объекта
        agent_types = user_info.get('types', '')
        if agent_types and str(prop_type) in agent_types.split(','):
            has_access = True
    
    # Форматируем текст карточки
    if is_agent and has_access:
        # Полная карточка для агента с доступом
        space_text = f"{space} кв.м" if space > 0 else "не указана"
        pricem_text = f" ({pricem:.1f} т.р./кв.м)" if space > 0 and pricem > 0 else ""
        
        text = (
            f"🏠 *{flat_type} в Геленджике*\n"
            f"📍 {address}\n\n"
            f"📏 *Площадь:* {space_text}{pricem_text}\n"
            f"💰 *Цена:* {format_price(price)} т.р.\n"
            f"🏢 *Этаж:* {floor}/{floors_total}\n"
            f"🖼 *Фото:* {photo_cnt} шт.\n"
            f"🕒 *Добавлено:* {created}\n"
            f"🔢 *Номер объявления:* `{ad_number}`"
        )
    else:
        # Сокращенная карточка
        space_text = f"{space} кв.м" if space > 0 else "не указана"
        
        text = (
            f"🏠 *{flat_type} в Геленджике*\n"
            f"📍 {address}\n\n"
            f"📏 *Площадь:* {space_text}\n"
            f"💰 *Цена:* {format_price(price)} т.р.\n"
            f"🏢 *Этаж:* {floor}/{floors_total}\n"
            f"🔢 *Номер объявления:* `{ad_number}`"
        )
    
    # Получаем фото
    photos = []
    if property_data.get('photocnt', 0) > 0:
        preview_photo = get_photo_path(property_data['id'], property_data['type'])
        if preview_photo:
            photos = [preview_photo]
    
    
    # Получаем ID пользователя из контекста
    user_id = user_info.get('id') if user_info else None
    
    # Формируем клавиатуру
    keyboard = None
    if property_data.get('photocnt', 0) > 0 or True:  # Всегда показывать избранное
        from bot.presentation.keyboards.search import details_keyboard
        keyboard = details_keyboard(property_data, user_id)
    
    return {
        "text": text,
        "photos": photos,
        "keyboard": keyboard
    }


def get_all_photos(property_data):
    """Возвращает список всех фото объекта"""
    prop_id = property_data['id']
    prop_type = property_data['type']
    photo_cnt = property_data.get('photocnt', 0)
    photos = []
    
    # Получаем превью (первое фото)
    preview = get_photo_path(prop_id, prop_type)
    if preview:
        photos.append(preview)
    
    # Получаем дополнительные фото
    additional = get_additional_photos(property_data)
    photos.extend(additional)
    
    # Возвращаем уникальные фото (на случай дублирования)
    return list(set(photos))[:photo_cnt]  # Ограничиваем общим количеством