# bot/presentation/keyboards/common.py


from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

def main_menu():
    return ReplyKeyboardMarkup([
        ['🔍 Поиск', '❤ Избранное'],
        ['💼 Мой кабинет', 'ℹ Помощь']
    ], resize_keyboard=True)

def help_menu():
    return ReplyKeyboardMarkup([
        ['🏠 Главная']
    ], resize_keyboard=True)

def property_details_keyboard(property_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton('📞 Контакты', callback_data=f'contacts_{property_id}'),
            InlineKeyboardButton('❤ Избранное', callback_data=f'fav_{property_id}')
        ],
        [
            InlineKeyboardButton('🔙 Вернуться к результатам', callback_data="back_to_search"),
            InlineKeyboardButton('🏠 Главное меню', callback_data="main_menu")
        ]
    ])

def pagination_keyboard(current_index, total_results):
    """Клавиатура для навигации по результатам поиска"""
    #  Кнопки "Показать еще" и "Новый поиск"
    buttons = []
    
    # Кнопка "Показать еще" справа
    if current_index < total_results:
        buttons.append(InlineKeyboardButton(f"🔍 Показать еще", callback_data="show_more"))
    
    # Кнопка "Новый поиск" слева
    buttons.append(InlineKeyboardButton("🔄 Новый поиск", callback_data="new_search"))
    
    # Формируем ряд кнопок
    return InlineKeyboardMarkup([buttons])


def back_to_search_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Вернуться к результатам", callback_data="back_to_search")]
    ])

def details_keyboard(property_id):
    """Клавиатура для просмотра деталей объекта"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📷 Показать все фото", callback_data=f"details_{property_id}")],
        [InlineKeyboardButton("❤️ В избранное", callback_data=f"fav_{property_id}")]
    ])


# bot/presentation/keyboards/common.py

def navigation_keyboard(has_more=False):
    """Клавиатура навигации внизу экрана"""
    buttons = []
    
    if has_more:
        buttons.append("🔍 Показать еще")
    
    buttons.append("🔄 Новый поиск")
    
    return ReplyKeyboardMarkup([buttons], resize_keyboard=True, one_time_keyboard=True)