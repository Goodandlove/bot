# bot\core\utils.py

import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def format_price(price):
    try:
        return "{:,}".format(int(price)).replace(",", " ")
    except (ValueError, TypeError):
        return str(price)

def format_date(date_str):
    try:
        for fmt in ("%Y-%m-%d %H:%M:%S", "%d.%m.%Y %H:%M", "%Y-%m-%d"):
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime("%d.%m.%Y %H:%M")
            except ValueError:
                continue
        return date_str
    except Exception:
        return date_str