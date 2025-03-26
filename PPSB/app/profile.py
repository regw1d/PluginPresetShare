from aiogram import types
from datetime import datetime
import logging
from config import DB_NAME
from database import get_db
from app.utils import message_id_storage

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def back_to_menu_keyboard():
    from app.handlers import back_to_menu_keyboard
    return back_to_menu_keyboard()

async def show_profile(user: types.User, message: types.Message):
    logger.info(f"Showing profile for user {user.id}")
    logger.info(f"user.username: {user.username}")
    logger.info(f"user.first_name: {user.first_name}")
    logger.info(f"user.id: {user.id}")
    logger.info(f"user.is_bot: {user.is_bot}")
    logger.info(f"message.chat.type: {message.chat.type}")

    if message.chat.type != 'private':
        logger.warning("Profile command used in non-private chat.")
        await message.answer("Пожалуйста, используйте команду /profile в приватном чате с ботом.")
        return

    db_instance = get_db()
    if db_instance is None or db_instance.name != DB_NAME:
        logger.error(f"Database is not initialized or incorrect DB name. Expected: {DB_NAME}")
        await message.answer("Ошибка: база данных не инициализирована.", reply_markup=back_to_menu_keyboard())
        return
    
    user_profile_collection = db_instance["user_profile"]
    presets_collection = db_instance["presets"]
    user_id = user.id
    
    try:
        db_user = await user_profile_collection.find_one({"user_id": user_id})
        current_username = user.username or user.first_name or f"User_{user_id}"
        if not db_user:
            user_data = {
                "user_id": user_id,
                "username": current_username,
                "first_name": user.first_name,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "quests_completed": 0,
                "presets_uploaded": 0,
                "reviews_written": 0,
                "balance": 100
            }
            await user_profile_collection.insert_one(user_data)
            db_user = user_data
            logger.info(f"Created new profile for user {user_id} with username {current_username}")
        else:
            if db_user["username"] != current_username:
                await user_profile_collection.update_one(
                    {"user_id": user_id},
                    {"$set": {"username": current_username}}
                )
                db_user["username"] = current_username
                logger.info(f"Updated username for user {user_id} to {current_username}")

        last_presets = await presets_collection.find({"creator_id": user_id}).sort("created_at", -1).limit(3).to_list(length=None)
        user_quests_collection = db_instance["user_quests"]
        last_quests = await user_quests_collection.find({"user_id": user_id, "completed": True}).sort("completed_at", -1).limit(3).to_list(length=None)
        
        presets_text = "Последние пресеты:\n" + "\n".join(p["name"] for p in last_presets) if last_presets else "Нет загруженных пресетов."
        quests_text = "Последние квесты:\n" + "\n".join(q["quest_id"] for q in last_quests) if last_quests else "Нет выполненных квестов."

        display_username = user.username or user.first_name or f"User_{user_id}"
        logger.info(f"Displaying profile with username: {display_username}")

        profile_text = (
            f"👤 Профиль пользователя @{display_username}\n"
            f"📛 Ник: @{display_username}\n"
            f"📅 Дата регистрации: {db_user['created_at']}\n\n"
            f"🏆 Статистика:\n"
            f"✅ Выполнено квестов: {db_user['quests_completed']}\n"
            f"📤 Загружено пресетов: {db_user['presets_uploaded']}\n"
            f"📝 Написано отзывов: {db_user['reviews_written']}\n"
            f"💰 Баланс коинов: {db_user['balance']}\n\n"
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
