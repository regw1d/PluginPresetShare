from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from datetime import datetime
import logging
from config import DB_NAME
from database import get_db
from app.utils import message_id_storage  # Обновляем импорт

review_router = Router()

class ReviewStates(StatesGroup):
    TEXT = State()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def back_to_menu_keyboard():
    from app.handlers import back_to_menu_keyboard
    return back_to_menu_keyboard()

@review_router.message(Command("review"))
async def start_review(message: Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} started writing a review.")
    db_instance = get_db()
    if db_instance is None:
        logger.error(f"Database '{DB_NAME}' is not initialized. Cannot process /review command.")
        await message.answer(f"Ошибка: база данных '{DB_NAME}' не инициализирована.")
        return
    user_profile_collection = db_instance["user_profile"]
    user_id = message.from_user.id
    try:
        user = await user_profile_collection.find_one({"user_id": user_id})
        if not user:
            await message.answer("Сначала используйте /start, чтобы создать профиль!")
            return
    except Exception as e:
        logger.error(f"Failed to check user profile for {user_id}: {e}")
        await message.answer("Ошибка при проверке профиля.")
        return
    await state.set_state(ReviewStates.TEXT)
    chat_id = message.chat.id
    text = "Напишите ваш отзыв о боте:"
    if chat_id in message_id_storage:
        try:
            await message.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id_storage[chat_id],
                text=text,
                reply_markup=back_to_menu_keyboard()
            )
            return
        except Exception as e:
            logger.warning(f"Failed to edit message {message_id_storage[chat_id]}: {e}")
    msg = await message.answer(text, reply_markup=back_to_menu_keyboard())
    if len(message_id_storage) > 1000:
        message_id_storage.clear()
    message_id_storage[chat_id] = msg.message_id

@review_router.message(ReviewStates.TEXT)
async def process_review(message: Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} submitted review: {message.text}")
    db_instance = get_db()
    if db_instance is None:
        logger.error(f"Database '{DB_NAME}' is not initialized. Cannot process review.")
        await message.answer(f"Ошибка: база данных '{DB_NAME}' не инициализирована.")
        return
    reviews_collection = db_instance["reviews"]
    user_profile_collection = db_instance["user_profile"]
    review_text = message.text.strip()
    if not review_text:
        await message.answer("Отзыв не может быть пустым. Попробуйте снова.")
        return
    user_id = message.from_user.id
    review_data = {
        "user_id": user_id,
        "username": message.from_user.username or message.from_user.first_name or "Без ника",
        "text": review_text,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    try:
        await reviews_collection.insert_one(review_data)
        user = await user_profile_collection.find_one({"user_id": user_id})
        if user:
            new_reviews = user["reviews_written"] + 1
            await user_profile_collection.update_one(
                {"user_id": user_id},
                {"$set": {"reviews_written": new_reviews}}
            )
        await message.answer("Спасибо за ваш отзыв!")
    except Exception as e:
        logger.error(f"Failed to save review for user {user_id}: {e}")
        await message.answer("Ошибка при сохранении отзыва.")
    await state.clear()