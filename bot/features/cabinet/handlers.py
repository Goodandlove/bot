# bot/features/cabinet/handlerimport logging



import logging
from telegram import Update
from telegram.ext import ContextTypes
from bot.presentation.keyboards.common import main_menu
from bot.core.redis_manager import RedisManager
from bot.core.states import States

logger = logging.getLogger(__name__)

async def show_cabinet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Заглушка для раздела Мой кабинет"""
    user = update.effective_user
    RedisManager().set_state(user.id, States.CABINET_MAIN)
    
    text = ""
    if context.user_data.get('type') == 'agent':
        text = (
            "👔 *Кабинет агента*\n\n"
            "Здесь вы сможете:\n"
            "- Управлять своими объявлениями\n"
            "- Просматривать статистику\n"
            "- Настраивать профиль\n\n"
            "Раздел в разработке, ожидайте обновления!"
        )
    else:
        text = (
            "👤 *Личный кабинет*\n\n"
            "Здесь вы сможете:\n"
            "- Просматривать историю запросов\n"
            "- Управлять подписками\n"
            "- Настраивать уведомления\n\n"
            "Раздел в разработке, ожидайте обновления!"
        )
    
    await update.message.reply_text(
        text,
        reply_markup=main_menu(),
        parse_mode='Markdown'
    )

async def show_favorites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Заглушка для раздела Избранное"""
    user = update.effective_user
    RedisManager().set_state(user.id, States.FAVORITES_VIEW)
    
    await update.message.reply_text(
        "❤️ Раздел 'Избранное' находится в разработке.\n\n"
        "Здесь вы сможете просматривать и управлять сохраненными объявлениями.\n"
        "Ожидайте обновления в ближайшее время!",
        reply_markup=main_menu()
    )