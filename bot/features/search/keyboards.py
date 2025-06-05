# bot\features\search\keyboards.py

from telegram import ReplyKeyboardMarkup

def room_selection():
    return ReplyKeyboardMarkup([['1', '2', '3'], ['4+', 'Студия']], resize_keyboard=True)

def price_selection():
    return ReplyKeyboardMarkup([['цена от', 'цена до'], ['от - до', 'Пропустить']], resize_keyboard=True)

# ... другие клавиатуры