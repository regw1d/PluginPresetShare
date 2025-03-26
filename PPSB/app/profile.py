from aiogram import Bot
from aiogram.types import Message
from datetime import datetime
import logging
from config import DB_NAME
from database import get_db
from app.utils import message_id_storage  # Обновляем импорт

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def back_to_menu_keyboard():
    from app.handlers import back_to_menu_keyboard
    return back_to_menu_keyboard()

async def show_profile(message: Message, bot: Bot = None):
    logger.info(f"Showing profile for user {message.from_user.id}")
    db_instance = get_db()
    if db_instance is None or db_instance.name != DB_NAME:
        logger.error(f"Database is not initialized or incorrect DB name. Expected: {DB_NAME}")
        await message.answer("Ошибка: база данных не инициализирована.", reply_markup=back_to_menu_keyboard())
        return
    
    user_profile_collection = db_instance["user_profile"]
    presets_collection = db_instance["presets"]
    user_id = message.from_user.id
    
    try:
        user = await user_profile_collection.find_one({"user_id": user_id})
        if not user:
            user_data = {
                "user_id": user_id,
                "username": message.from_user.username or message.from_user.first_name or "Без ника",
                "first_name": message.from_user.first_name,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "quests_completed": 0,
                "presets_uploaded": 0,
                "reviews_written": 0,
                "balance": 100
            }
            await user_profile_collection.insert_one(user_data)
            user = user_data

        last_presets = await presets_collection.find({"creator_id": user_id}).sort("created_at", -1).limit(3).to_list(length=None)
        user_quests_collection = db_instance["user_quests"]
        last_quests = await user_quests_collection.find({"user_id": user_id, "completed": True}).sort("completed_at", -1).limit(3).to_list(length=None)
        
        presets_text = "Последние пресеты:\n" + "\n".join(p["name"] for p in last_presets) if last_presets else "Нет загруженных пресетов."
        quests_text = "Последние квесты:\n" + "\n".join(q["quest_id"] for q in last_quests) if last_quests else "Нет выполненных квестов."

        profile_text = (
            f"👤 Профиль пользователя @{user['username']}\n"
            f"📛 Ник: @{user['username']}\n"
            f"📅 Дата регистрации: {user['created_at']}\n\n"
            f"🏆 Статистика:\n"
            f"✅ Выполнено квестов: {user['quests_completed']}\n"
            f"📤 Загружено пресетов: {user['presets_uploaded']}\n"
            f"📝 Написано отзывов: {user['reviews_written']}\n"
            f"💰 Баланс коинов: {user['balance']}\n\n"
            f"{presets_text}\n\n"
            f"{quests_text}"
        )
        chat_id = message.chat.id
        if chat_id in message_id_storage:
            try:
                await message.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id_storage[chat_id],
                    text=profile_text,
                    reply_markup=back_to_menu_keyboard()
                )
                return
            except Exception as e:
                logger.warning(f"Failed to edit message {message_id_storage[chat_id]}: {e}")

        msg = await message.answer(profile_text, reply_markup=back_to_menu_keyboard())
        if len(message_id_storage) > 1000:
            message_id_storage.clear()
        message_id_storage[chat_id] = msg.message_id
    except Exception as e:
        logger.error(f"Failed to show profile for user {user_id}: {e}")
        await message.answer("Ошибка при загрузке профиля.", reply_markup=back_to_menu_keyboard())