from aiogram import Router, F, Bot
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import CommandStart, Command
from config import GITHUB, DONATE, CHANNEL, DB_NAME
from app.quests import show_quests_menu, list_quests, start_create_quest
from app.presets import start_upload_preset, list_presets
from app.review import start_review
from app.profile import show_profile
import logging
from aiogram.fsm.context import FSMContext
from datetime import datetime
from database import get_db
from app.utils import message_id_storage

router = Router()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Вернуться в меню", callback_data="back_to_menu")]
    ])

def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Создать квест 🎮", callback_data="create_quest"),
         InlineKeyboardButton(text="Мои квесты 📋", callback_data="my_quests")],
        [InlineKeyboardButton(text="Профиль 👤", callback_data="profile"),
         InlineKeyboardButton(text="Помощь 💡", callback_data="help")],
        [InlineKeyboardButton(text="Загрузить пресет 🎧", callback_data="upload_preset"),
         InlineKeyboardButton(text="Скачать пресет 📥", callback_data="list_presets")],
        [InlineKeyboardButton(text="Оставить отзыв ✍️", callback_data="review"),
         InlineKeyboardButton(text="Список квестов 🔍", callback_data="quests")],
        [InlineKeyboardButton(text="Лидерская доска 🏆", callback_data="leaderboard"),
         InlineKeyboardButton(text="GitHub 🛠️", callback_data="github")],
        [InlineKeyboardButton(text="Поддержать 💸", callback_data="donate"),
         InlineKeyboardButton(text="Канал 📣", callback_data="channel")]
    ])

@router.message(CommandStart())
async def start(message: Message):
    logger.info(f"User {message.from_user.id} used /start command.")
    db_instance = get_db()
    if db_instance is None:
        logger.error(f"Database '{DB_NAME}' is not initialized. Cannot process /start command.")
        await message.answer(f"Ошибка: база данных '{DB_NAME}' не инициализирована. Пожалуйста, обратитесь к администратору.")
        return
    user_profile_collection = db_instance["user_profile"]
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
            logger.info(f"Created new profile for user {user_id} with balance 100.")
    except Exception as e:
        logger.error(f"Failed to process /start for user {user_id}: {e}")
        await message.answer("Ошибка при обработке команды /start.")
        return

    keyboard = main_menu_keyboard()
    text = (
        "🎵 Добро пожаловать в мир звука и творчества! 🎵\n\n"
        "Здесь вы можете:\n"
        "✨ Создавать уникальные квесты для музыкантов.\n"
        "🎯 Участвовать в интересных заданиях.\n"
        "🎧 Загружать и скачивать пресеты.\n"
        "📝 Оставлять отзывы и помогать развитию проекта.\n\n"
        "Выберите действие:"
    )
    chat_id = message.chat.id
    if chat_id in message_id_storage:
        try:
            await message.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id_storage[chat_id],
                text=text,
                reply_markup=keyboard
            )
            return
        except Exception as e:
            logger.warning(f"Failed to edit message {message_id_storage[chat_id]}: {e}")

    msg = await message.answer(text, reply_markup=keyboard)
    if len(message_id_storage) > 1000:
        message_id_storage.clear()
    message_id_storage[chat_id] = msg.message_id

@router.message(Command("leaderboard"))
async def leaderboard_command(message: Message):
    logger.info(f"User {message.from_user.id} used /leaderboard command.")
    db_instance = get_db()
    if db_instance is None:
        logger.error(f"Database '{DB_NAME}' is not initialized. Cannot process /leaderboard command.")
        await message.answer(f"Ошибка: база данных '{DB_NAME}' не инициализирована.")
        return
    user_profile_collection = db_instance["user_profile"]
    try:
        top_users = await user_profile_collection.aggregate([
            {"$sort": {"quests_completed": -1}},
            {"$limit": 10}
        ]).to_list(length=None)
        if not top_users:
            await message.answer("Пока нет лидеров.", reply_markup=back_to_menu_keyboard())
            return
        leaderboard_text = "🏆 Топ-10 пользователей по выполненным квестам:\n\n"
        for i, user in enumerate(top_users, 1):
            leaderboard_text += f"{i}. @{user['username']} - {user['quests_completed']} квестов\n"
        await message.answer(leaderboard_text, reply_markup=back_to_menu_keyboard())
    except Exception as e:
        logger.error(f"Failed to fetch leaderboard: {e}")
        await message.answer("Ошибка при загрузке лидерской доски.")

@router.message(Command("rate_preset"))
async def rate_preset_command(message: Message):
    logger.info(f"User {message.from_user.id} used /rate_preset command: {message.text}")
    db_instance = get_db()
    if db_instance is None:
        logger.error(f"Database '{DB_NAME}' is not initialized. Cannot process /rate_preset command.")
        await message.answer(f"Ошибка: база данных '{DB_NAME}' не инициализирована.")
        return
    presets_collection = db_instance["presets"]
    try:
        _, preset_name, rating = message.text.split(maxsplit=2)
        rating = int(rating)
        if not (1 <= rating <= 5):
            raise ValueError("Рейтинг должен быть от 1 до 5.")
    except ValueError as e:
        await message.answer(f"Ошибка: {e}. Используйте формат: /rate_preset <preset_name> <rating>", reply_markup=back_to_menu_keyboard())
        return

    try:
        preset = await presets_collection.find_one({"name": preset_name})
        if not preset:
            await message.answer("Пресет не найден.", reply_markup=back_to_menu_keyboard())
            return

        user_id = message.from_user.id
        ratings = preset.get("ratings", [])
        if any(r["user_id"] == user_id for r in ratings):
            await message.answer("Вы уже оценили этот пресет.", reply_markup=back_to_menu_keyboard())
            return

        ratings.append({"user_id": user_id, "rating": rating})
        avg_rating = sum(r["rating"] for r in ratings) / len(ratings)
        await presets_collection.update_one(
            {"name": preset_name},
            {"$set": {"ratings": ratings, "avg_rating": avg_rating}}
        )
        await message.answer(f"Спасибо за оценку! Средний рейтинг {preset_name}: {avg_rating:.1f}", reply_markup=back_to_menu_keyboard())
    except Exception as e:
        logger.error(f"Failed to rate preset '{preset_name}': {e}")
        await message.answer("Ошибка при оценке пресета.")

# Обновленные callback-обработчики
@router.callback_query(F.data == "create_quest")
async def handle_create_quest_callback(callback: CallbackQuery, state: FSMContext):
    logger.info(f"User {callback.from_user.id} clicked 'Создать квест 🎮'.")
    await start_create_quest(callback.message, state)
    await callback.answer()

@router.callback_query(F.data == "profile")
async def handle_profile_callback(callback: CallbackQuery):
    logger.info(f"User {callback.from_user.id} clicked 'Профиль 👤'.")
    await show_profile(callback.message)
    await callback.answer()

@router.callback_query(F.data == "upload_preset")
async def handle_upload_preset_callback(callback: CallbackQuery, state: FSMContext):
    logger.info(f"User {callback.from_user.id} clicked 'Загрузить пресет 🎧'.")
    await start_upload_preset(callback.message, state)
    await callback.answer()

@router.callback_query(F.data == "review")
async def handle_review_callback(callback: CallbackQuery, state: FSMContext):
    logger.info(f"User {callback.from_user.id} clicked 'Оставить отзыв ✍️'.")
    await start_review(callback.message, state)
    await callback.answer()

@router.callback_query(F.data == "list_presets")
async def handle_list_presets_callback(callback: CallbackQuery):
    logger.info(f"User {callback.from_user.id} clicked 'Скачать пресет 📥'.")
    await list_presets(callback.message)
    await callback.answer()

@router.callback_query(F.data == "quests")
async def handle_quests_callback(callback: CallbackQuery):
    logger.info(f"User {callback.from_user.id} clicked 'Список квестов 🔍'.")
    await show_quests_menu(callback.message)
    await callback.answer()

@router.callback_query(F.data == "my_quests")
async def handle_my_quests_callback(callback: CallbackQuery):
    logger.info(f"User {callback.from_user.id} clicked 'Мои квесты 📋'.")
    db_instance = get_db()
    if db_instance is None:
        logger.error(f"Database '{DB_NAME}' is not initialized. Cannot process my_quests callback.")
        await callback.message.answer(f"Ошибка: база данных '{DB_NAME}' не инициализирована.")
        return
    await list_quests(
        message=callback.message,
        is_my_quests=True,
        user_id=callback.from_user.id,
        db_instance=db_instance
    )
    await callback.answer()

@router.callback_query(F.data == "help")
async def handle_help_callback(callback: CallbackQuery):
    logger.info(f"User {callback.from_user.id} clicked 'Помощь 💡'.")
    await handle_help(callback.message)
    await callback.answer()

@router.callback_query(F.data == "leaderboard")
async def handle_leaderboard_callback(callback: CallbackQuery):
    logger.info(f"User {callback.from_user.id} clicked 'Лидерская доска 🏆'.")
    db_instance = get_db()
    if db_instance is None:
        logger.error(f"Database '{DB_NAME}' is not initialized. Cannot process leaderboard callback.")
        await callback.message.answer(f"Ошибка: база данных '{DB_NAME}' не инициализирована.")
        return
    user_profile_collection = db_instance["user_profile"]
    try:
        top_users = await user_profile_collection.aggregate([
            {"$sort": {"quests_completed": -1}},
            {"$limit": 10}
        ]).to_list(length=None)
        if not top_users:
            await callback.message.answer("Пока нет лидеров.", reply_markup=back_to_menu_keyboard())
            return
        leaderboard_text = "🏆 Топ-10 пользователей по выполненным квестам:\n\n"
        for i, user in enumerate(top_users, 1):
            leaderboard_text += f"{i}. @{user['username']} - {user['quests_completed']} квестов\n"
        await callback.message.answer(leaderboard_text, reply_markup=back_to_menu_keyboard())
    except Exception as e:
        logger.error(f"Failed to fetch leaderboard: {e}")
        await callback.message.answer("Ошибка при загрузке лидерской доски.")
    await callback.answer()

@router.callback_query(F.data == "github")
async def handle_github_callback(callback: CallbackQuery):
    logger.info(f"User {callback.from_user.id} clicked 'GitHub 🛠️'.")
    await callback.message.answer(f"Ссылка на GitHub: {GITHUB}\n\n", reply_markup=back_to_menu_keyboard())
    await callback.answer()

@router.callback_query(F.data == "donate")
async def handle_donate_callback(callback: CallbackQuery):
    logger.info(f"User {callback.from_user.id} clicked 'Поддержать 💸'.")
    await callback.message.answer(f"Ссылка для поддержки: {DONATE}\n\n", reply_markup=back_to_menu_keyboard())
    await callback.answer()

@router.callback_query(F.data == "channel")
async def handle_channel_callback(callback: CallbackQuery):
    logger.info(f"User {callback.from_user.id} clicked 'Канал 📣'.")
    await callback.message.answer(f"Ссылка на канал: {CHANNEL}\n\n", reply_markup=back_to_menu_keyboard())
    await callback.answer()

@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    logger.info(f"User {callback.from_user.id} returned to main menu.")
    chat_id = callback.message.chat.id
    text = (
        "🎵 Добро пожаловать в мир звука и творчества! 🎵\n\n"
        "Здесь вы можете:\n"
        "✨ Создавать уникальные квесты для музыкантов.\n"
        "🎯 Участвовать в интересных заданиях.\n"
        "🎧 Загружать и скачивать пресеты.\n"
        "📝 Оставлять отзывы и помогать развитию проекта.\n\n"
        "Выберите действие:"
    )
    if chat_id in message_id_storage:
        try:
            await callback.message.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id_storage[chat_id],
                text=text,
                reply_markup=main_menu_keyboard()
            )
            await callback.answer("Вернулись в главное меню.")
            return
        except Exception as e:
            logger.warning(f"Failed to edit message {message_id_storage[chat_id]}: {e}")
    msg = await callback.message.answer(text, reply_markup=main_menu_keyboard())
    if len(message_id_storage) > 1000:
        message_id_storage.clear()
    message_id_storage[chat_id] = msg.message_id
    await callback.answer("Вернулись в главное меню.")

@router.message(Command('help'))
async def help_command(message: Message):
    await handle_help(message)

@router.message(Command('github'))
async def github(message: Message):
    logger.info(f"User {message.from_user.id} used /github command.")
    await message.answer(f"Ссылка на GitHub: {GITHUB}\n\n", reply_markup=back_to_menu_keyboard())

@router.message(Command('donate'))
async def donate(message: Message):
    logger.info(f"User {message.from_user.id} used /donate command.")
    await message.answer(f"Ссылка для поддержки: {DONATE}\n\n", reply_markup=back_to_menu_keyboard())

@router.message(Command('profile'))
async def profile_command(message: Message):
    logger.info(f"User {message.from_user.id} used /profile command.")
    await show_profile(message)

async def handle_help(message: Message):
    logger.info(f"User {message.from_user.id} used /help command.")
    chat_id = message.chat.id
    text = (
        "📚 Справка по использованию бота:\n\n"
        "/start – Главное меню.\n"
        "/help – Эта страница с подсказками.\n"
        "/github – Исходный код проекта.\n"
        "/donate – Поддержите развитие проекта.\n"
        "/create_quest – Создайте новый квест.\n"
        "/profile – Просмотр профиля.\n"
        "/quests – Список квестов.\n"
        "/upload_preset – Загрузите пресет.\n"
        "/list_presets – Список пресетов.\n"
        "/rate_preset – Оценить пресет.\n"
        "/review – Напишите отзыв.\n"
        "/leaderboard – Топ пользователей.\n"
        "/channel – Наш канал.\n\n"
        "🌟 Вместе создаем инструмент для музыкантов!\n\n"
    )
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
