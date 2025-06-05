# bot\core\states.py


from enum import Enum

class States(Enum):
    MAIN_MENU = 0
    HELP_MENU = 1
    SEARCH_ROOMS = 10
    SEARCH_PRICE = 11
    SEARCH_PRICE_MIN = 12
    SEARCH_PRICE_MAX = 13
    SEARCH_FLOOR = 14
    VIEWING_RESULTS = 20
    VIEWING_DETAILS = 21
    CABINET_MAIN = 30
    FAVORITES_VIEW = 40