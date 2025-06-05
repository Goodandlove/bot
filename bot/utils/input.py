# bot/utils/input.py
# Утилиты ввода

import re

def extract_numbers(input_text, max_values=2):
    """Извлекает числа из текста"""
    # Удаляем все символы, кроме цифр, пробелов, дефисов, запятых и точек
    cleaned = re.sub(r'[^\d\s\-,\.=]', '', input_text)
    
    # Заменяем запятые на точки
    cleaned = cleaned.replace(',', '.')
    
    # Ищем все последовательности цифр
    numbers = []
    for match in re.finditer(r'\d+', cleaned):
        try:
            num = int(match.group())
            numbers.append(num)
            if len(numbers) >= max_values:
                break
        except ValueError:
            continue
    
    return numbers

def parse_price_input(input_text, input_type="range"):
    """Парсит ввод цен с обработкой различных форматов"""
    numbers = extract_numbers(input_text, 2)
    result = {"min": None, "max": None}
    
    # Поддержка точного значения
    if "=" in input_text:
        if numbers:
            result["min"] = numbers[0]
            result["max"] = numbers[0]
            return result
    
    # Обработка по типу ввода
    if input_type == "min":
        if numbers:
            result["min"] = numbers[0]
    elif input_type == "max":
        if numbers:
            result["max"] = numbers[0]
    else:  # range
        if numbers:
            result["min"] = numbers[0]
            if len(numbers) > 1:
                result["max"] = numbers[1]
    
    # Автокоррекция: если min > max, меняем местами
    if result["min"] is not None and result["max"] is not None:
        if result["min"] > result["max"]:
            result["min"], result["max"] = result["max"], result["min"]
    
    return result