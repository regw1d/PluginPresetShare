from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Document, User
from aiogram.filters import Command, Filter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from datetime import datetime, timedelta
import logging
from config import DB_NAME
from database import get_db
from app.utils import message_id_storage  # Импортируем из нового модуля

quest_router = Router()

class CreateQuestStates(StatesGroup):
    TITLE = State()
    DESCRIPTION = State()
    REWARD = State()
    GENRE = State()
    DEADLINE = State()

class PresetStates(StatesGroup):
    WAITING_FOR_PRESET = State()

GENRES = [
    "Rock", "Pop", "Jazz", "Classical", "Electronic", "Hip-Hop", "R&B", "Country",
    "Blues", "Folk", "Metal", "Indie", "Alternative", "Reggae", "Soul", "Disco"
]

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def _get_back_to_menu_keyboard():
    from app.handlers import back_to_menu_keyboard
    return back_to_menu_keyboard()

async def ensure_user_profile(user_id: int, telegram_user: User = None, db_instance=None):
    if db_instance is None:
        db_instance = get_db()
    if db_instance is None or db_instance.name != DB_NAME:
        logger.error(f"Database is not initialized or incorrect DB name. Expected: {DB_NAME}")
        return None
    user_profile_collection = db_instance["user_profile"]
    try:
        user = await user_profile_collection.find_one({"user_id": int(user_id)})
        if not user:
            username = getattr(telegram_user, 'username', "Без ника") if telegram_user else "Без ника"
            first_name = getattr(telegram_user, 'first_name', "") if telegram_user else ""
            user_data = {
                "user_id": int(user_id),
                "username": username,
                "first_name": first_name,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "quests_completed": 0,
                "presets_uploaded": 0,
                "reviews_written": 0,
                "balance": 100
            }
            await user_profile_collection.insert_one(user_data)
            logger.info(f"Created new profile for user {user_id} with balance 100.")
        return await user_profile_collection.find_one({"user_id": int(user_id)})
    except Exception as e:
        logger.error(f"Failed to ensure profile for user {user_id}: {e}")
        return None

async def get_username(user_id: int, db_instance) -> str:
    if db_instance is None:
        db_instance = get_db()
    if db_instance is None or db_instance.name != DB_NAME:
        logger.error(f"Database is not initialized or incorrect DB name. Expected: {DB_NAME}")
        return "Неизвестный пользователь"
    user_profile_collection = db_instance["user_profile"]
    try:
        user = await user_profile_collection.find_one({"user_id": int(user_id)})
        return user.get("username", "Неизвестный пользователь") if user else "Неизвестный пользователь"
    except Exception as e:
        logger.error(f"Failed to get username for user {user_id}: {e}")
        return "Неизвестный пользователь"

@quest_router.message(Command("create_quest"))
async def start_create_quest(message: Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} started creating a new quest.")
    db_instance = get_db()
    if db_instance is None or db_instance.name != DB_NAME:
        logger.error(f"Database is not initialized or incorrect DB name. Expected: {DB_NAME}")
        await message.answer("Ошибка: база данных не инициализирована.")
        return
    user_id = int(message.from_user.id)
    user = await ensure_user_profile(user_id, message.from_user, db_instance)
    if not user:
        await message.answer("Произошла ошибка при создании профиля. Попробуйте позже!")
        return
    await state.set_state(CreateQuestStates.TITLE)
    chat_id = message.chat.id
    text = "Шаг 1/5: Введите название квеста."
    if chat_id in message_id_storage:
        try:
            await message.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id_storage[chat_id],
                text=text,
                reply_markup=_get_back_to_menu_keyboard()
            )
            return
        except Exception as e:
            logger.warning(f"Failed to edit message {message_id_storage[chat_id]}: {e}")
    msg = await message.answer(text, reply_markup=_get_back_to_menu_keyboard())
    if len(message_id_storage) > 1000:
        message_id_storage.clear()
    message_id_storage[chat_id] = msg.message_id

@quest_router.message(CreateQuestStates.TITLE)
async def process_title(message: Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} entered title: {message.text}")
    title = message.text.strip()
    if not title:
        await message.answer("Название не может быть пустым. Попробуйте снова.")
        return
    await state.update_data(title=title)
    await message.answer("Шаг 2/5: Введите описание квеста.")
    await state.set_state(CreateQuestStates.DESCRIPTION)

@quest_router.message(CreateQuestStates.DESCRIPTION)
async def process_description(message: Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} entered description: {message.text}")
    description = message.text.strip()
    if not description:
        await message.answer("Описание не может быть пустым. Попробуйте снова.")
        return
    await state.update_data(description=description)
    await message.answer("Шаг 3/5: Введите награду за выполнение квеста (в коинах).")
    await state.set_state(CreateQuestStates.REWARD)

@quest_router.message(CreateQuestStates.REWARD)
async def process_reward(message: Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} entered reward: {message.text}")
    db_instance = get_db()
    if db_instance is None or db_instance.name != DB_NAME:
        logger.error(f"Database is not initialized or incorrect DB name. Expected: {DB_NAME}")
        await message.answer("Ошибка: база данных не инициализирована.")
        return
    reward = message.text.strip()
    try:
        reward = int(reward)
        if reward <= 0:
            await message.answer("Награда должна быть положительным числом. Попробуйте снова.")
            return
    except ValueError:
        await message.answer("Награда должна быть числом. Попробуйте снова.")
        return
    user_id = int(message.from_user.id)
    user = await ensure_user_profile(user_id, message.from_user, db_instance)
    if not user or user["balance"] < reward:
        await message.answer("У вас недостаточно коинов для создания квеста с такой наградой!")
        await state.clear()
        return
    await state.update_data(reward=reward)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=genre, callback_data=f"genre_{genre}")] for genre in GENRES[:10]
    ])
    await message.answer("Шаг 4/5: Выберите музыкальный жанр для квеста.", reply_markup=keyboard)
    await state.set_state(CreateQuestStates.GENRE)

@quest_router.callback_query(F.data.startswith("genre_"), CreateQuestStates.GENRE)
async def process_genre(callback: CallbackQuery, state: FSMContext):
    logger.info(f"User {callback.from_user.id} selected genre: {callback.data.split('_')[1]}")
    genre = callback.data.split("_")[1]
    await state.update_data(genre=genre)
    await callback.message.answer("Шаг 5/5: Хотите установить дедлайн? (да/нет)", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Да", callback_data="deadline_yes"), InlineKeyboardButton(text="Нет", callback_data="deadline_no")]
    ]))
    await state.set_state(CreateQuestStates.DEADLINE)
    await callback.answer()

@quest_router.callback_query(F.data == "deadline_yes", CreateQuestStates.DEADLINE)
async def process_deadline_yes(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите количество дней для дедлайна (например, 7):")
    await callback.answer()

@quest_router.callback_query(F.data == "deadline_no", CreateQuestStates.DEADLINE)
async def process_deadline_no(callback: CallbackQuery, state: FSMContext):
    db_instance = get_db()
    if db_instance is None or db_instance.name != DB_NAME:
        logger.error(f"Database is not initialized or incorrect DB name. Expected: {DB_NAME}")
        await callback.message.answer("Ошибка: база данных не инициализирована.")
        return
    try:
        await create_quest(callback, state, None, db_instance)
    except Exception as e:
        logger.error(f"Failed to process deadline_no for user {callback.from_user.id}: {e}")
        await callback.message.answer("Ошибка при создании квеста.")
    await callback.answer()

@quest_router.message(CreateQuestStates.DEADLINE)
async def process_deadline(message: Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} entered deadline: {message.text}")
    db_instance = get_db()
    if db_instance is None or db_instance.name != DB_NAME:
        logger.error(f"Database is not initialized or incorrect DB name. Expected: {DB_NAME}")
        await message.answer("Ошибка: база данных не инициализирована.")
        return
    try:
        days = int(message.text.strip())
        if days <= 0:
            await message.answer("Дедлайн должен быть положительным числом. Попробуйте снова.")
            return
        deadline = datetime.now() + timedelta(days=days)
        await create_quest(message, state, deadline, db_instance)
    except ValueError:
        await message.answer("Дедлайн должен быть числом. Попробуйте снова.")
    except Exception as e:
        logger.error(f"Failed to process deadline for user {message.from_user.id}: {e}")
        await message.answer("Ошибка при создании квеста с дедлайном.")

async def create_quest(source: Message | CallbackQuery, state: FSMContext, deadline: datetime | None, db_instance):
    if db_instance is None:
        db_instance = get_db()
    if db_instance is None or db_instance.name != DB_NAME:
        logger.error(f"Database is not initialized or incorrect DB name. Expected: {DB_NAME}")
        await source.answer("Ошибка: база данных не инициализирована.", reply_markup=_get_back_to_menu_keyboard())
        return
    data = await state.get_data()
    user_id = int(source.from_user.id)
    reward = data["reward"]

    user = await ensure_user_profile(user_id, source.from_user, db_instance)
    if not user or user["balance"] < reward:
        await source.answer("У вас недостаточно коинов!", reply_markup=_get_back_to_menu_keyboard())
        await state.clear()
        return

    new_balance = user["balance"] - reward
    quest_id = f"Quest_{user_id}_{int(datetime.now().timestamp())}"
    quest_data = {
        "quest_id": quest_id,
        "title": data["title"],
        "description": data["description"],
        "reward": reward,
        "genre": data["genre"],
        "category": data["genre"],
        "creator_id": user_id,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "active",
        "deadline": deadline.strftime("%Y-%m-%d %H:%M:%S") if deadline else None
    }

    try:
        await db_instance["user_profile"].update_one(
            {"user_id": user_id},
            {"$set": {"balance": new_balance}}
        )
        await db_instance["quests"].insert_one(quest_data)
        logger.info(f"Quest created with ID: {quest_id} for user {user_id}")
        deadline_text = f" Дедлайн: {deadline.strftime('%Y-%m-%d %H:%M:%S')}" if deadline else ""
        await source.answer(
            f"Квест '{data['title']}' создан! Снято {reward} коинов. Баланс: {new_balance}{deadline_text}",
            reply_markup=_get_back_to_menu_keyboard()
        )
    except Exception as e:
        logger.error(f"Failed to create quest with ID {quest_id}: {e}")
        await source.answer("Ошибка при создании квеста.", reply_markup=_get_back_to_menu_keyboard())
    await state.clear()

@quest_router.message(Command("quests"))
async def show_quests_menu(message: Message, db_instance=None):
    logger.info(f"User {message.from_user.id} requested quests menu.")
    if db_instance is None:
        db_instance = get_db()
    if db_instance is None or db_instance.name != DB_NAME:
        logger.error(f"Database is not initialized or incorrect DB name. Expected: {DB_NAME}")
        await message.answer("Ошибка: база данных не инициализирована.")
        return
    user_id = int(message.from_user.id)
    try:
        await ensure_user_profile(user_id, message.from_user, db_instance)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Список квестов", callback_data="quests_list"),
             InlineKeyboardButton(text="Принятые квесты", callback_data="accepted_quests"),
             InlineKeyboardButton(text="Ваши квесты", callback_data="my_quests")]
        ])
        chat_id = message.chat.id
        if chat_id in message_id_storage:
            try:
                await message.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id_storage[chat_id],
                    text="Выберите категорию:",
                    reply_markup=keyboard
                )
                return
            except Exception as e:
                logger.warning(f"Failed to edit message {message_id_storage[chat_id]}: {e}")
        msg = await message.answer("Выберите категорию:", reply_markup=keyboard)
        if len(message_id_storage) > 1000:
            message_id_storage.clear()
        message_id_storage[chat_id] = msg.message_id
    except Exception as e:
        logger.error(f"Failed to show quests menu for user {user_id}: {e}")
        await message.answer("Ошибка при загрузке меню квестов.")

@quest_router.callback_query(F.data == "quests_list")
async def list_available_quests(callback: CallbackQuery):
    logger.info(f"User {callback.from_user.id} requested list of available quests.")
    db_instance = get_db()
    if db_instance is None or db_instance.name != DB_NAME:
        logger.error(f"Database is not initialized or incorrect DB name. Expected: {DB_NAME}")
        await callback.message.answer("Ошибка: база данных не инициализирована.")
        return
    user_id = int(callback.from_user.id)
    try:
        await ensure_user_profile(user_id, callback.from_user, db_instance)
        await callback.message.answer(
            "Список доступных квестов:\n\n",
            reply_markup=_get_back_to_menu_keyboard()
        )
        await list_quests(callback.message, is_my_quests=False, user_id=user_id, db_instance=db_instance)
    except Exception as e:
        logger.error(f"Failed to list available quests for user {user_id}: {e}")
        await callback.message.answer("Ошибка при загрузке списка квестов.")
    await callback.answer()

@quest_router.callback_query(F.data == "accepted_quests")
async def list_accepted_quests(callback: CallbackQuery):
    logger.info(f"User {callback.from_user.id} requested list of accepted quests.")
    db_instance = get_db()
    if db_instance is None or db_instance.name != DB_NAME:
        logger.error(f"Database is not initialized or incorrect DB name. Expected: {DB_NAME}")
        await callback.message.answer("Ошибка: база данных не инициализирована.")
        return
    user_id = int(callback.from_user.id)
    try:
        await ensure_user_profile(user_id, callback.from_user, db_instance)
        accepted_quests = await db_instance["user_quests"].find({"user_id": user_id, "completed": False}).to_list(length=None)
        if not accepted_quests:
            await callback.message.answer("У вас нет принятых квестов.", reply_markup=_get_back_to_menu_keyboard())
            await callback.answer()
            return
        quests_text = "\n\n".join([f"<b>{await get_quest_title(quest['quest_id'], db_instance)}</b>\nID: {quest['quest_id']}" for quest in accepted_quests])
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"Отправить пресет для {await get_quest_title(quest['quest_id'], db_instance)}", callback_data=f"submit_preset_file_{quest['quest_id']}")]
            for quest in accepted_quests
        ])
        keyboard.inline_keyboard.append([InlineKeyboardButton(text="Вернуться в меню", callback_data="back_to_menu")])
        await callback.message.answer(f"Ваши принятые квесты:\n\n{quests_text}", reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Failed to list accepted quests for user {user_id}: {e}")
        await callback.message.answer("Ошибка при загрузке принятых квестов.")
    await callback.answer()

@quest_router.callback_query(F.data == "my_quests")
async def list_my_quests(callback: CallbackQuery):
    logger.info(f"User {callback.from_user.id} requested list of their quests.")
    db_instance = get_db()
    if db_instance is None or db_instance.name != DB_NAME:
        logger.error(f"Database is not initialized or incorrect DB name. Expected: {DB_NAME}")
        await callback.message.answer("Ошибка: база данных не инициализирована.")
        return
    user_id = int(callback.from_user.id)
    try:
        await ensure_user_profile(user_id, callback.from_user, db_instance)
        await list_quests(callback.message, is_my_quests=True, user_id=user_id, db_instance=db_instance)
    except Exception as e:
        logger.error(f"Failed to list my quests for user {user_id}: {e}")
        await callback.message.answer("Ошибка при загрузке ваших квестов.")
    await callback.answer()

async def get_quest_title(quest_id: str, db_instance) -> str:
    if db_instance is None:
        db_instance = get_db()
    if db_instance is None or db_instance.name != DB_NAME:
        logger.error(f"Database is not initialized or incorrect DB name. Expected: {DB_NAME}")
        return "Квест не найден"
    quests_collection = db_instance["quests"]
    try:
        quest = await quests_collection.find_one({"quest_id": quest_id})
        return quest.get('title', 'Нет названия') if quest else 'Квест не найден'
    except Exception as e:
        logger.error(f"Failed to get quest title for quest_id {quest_id}: {e}")
        return 'Квест не найден'

@quest_router.callback_query(F.data.startswith("submit_preset_file_"))
async def process_submit_preset_request(callback: CallbackQuery, state: FSMContext):
    logger.info(f"User {callback.from_user.id} requested to submit a preset file for quest: {callback.data}")
    db_instance = get_db()
    if db_instance is None or db_instance.name != DB_NAME:
        logger.error(f"Database is not initialized or incorrect DB name. Expected: {DB_NAME}")
        await callback.message.answer("Ошибка: база данных не инициализирована.")
        return
    quest_id = callback.data.split("submit_preset_file_")[1]
    user_id = int(callback.from_user.id)
    
    try:
        user = await ensure_user_profile(user_id, callback.from_user, db_instance)
        if not user:
            await callback.message.answer("Ошибка с профилем.", reply_markup=_get_back_to_menu_keyboard())
            await state.clear()
            await callback.answer()
            return
        
        user_quest = await db_instance["user_quests"].find_one({"user_id": user_id, "quest_id": quest_id, "completed": False})
        if not user_quest:
            await callback.message.answer("Вы не приняли этот квест или он завершен.", reply_markup=_get_back_to_menu_keyboard())
            await state.clear()
            await callback.answer()
            return
        
        quest = await db_instance["quests"].find_one({"quest_id": quest_id})
        if not quest or quest.get("status") != "active":
            await callback.message.answer(f"Квест с ID {quest_id} не активен.", reply_markup=_get_back_to_menu_keyboard())
            await state.clear()
            await callback.answer()
            return
        
        await callback.message.answer("Прикрепите файл пресета для этого квеста.", reply_markup=_get_back_to_menu_keyboard())
        await state.set_state(PresetStates.WAITING_FOR_PRESET)
        await state.update_data(quest_id=quest_id, user_id=user_id)
    except Exception as e:
        logger.error(f"Failed to process submit preset request for quest {quest_id}: {e}")
        await callback.message.answer("Ошибка при обработке запроса на отправку пресета.")
    await callback.answer()

@quest_router.message(PresetStates.WAITING_FOR_PRESET, F.document)
async def process_preset_file(message: Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} submitted a preset file: {message.document.file_name}")
    db_instance = get_db()
    if db_instance is None or db_instance.name != DB_NAME:
        logger.error(f"Database is not initialized or incorrect DB name. Expected: {DB_NAME}")
        await message.answer("Ошибка: база данных не инициализирована.")
        return
    user_id = int(message.from_user.id)
    data = await state.get_data()
    quest_id = data.get("quest_id")
    if not quest_id:
        await message.answer("Ошибка. Выберите квест снова.", reply_markup=_get_back_to_menu_keyboard())
        await state.clear()
        return
    
    try:
        user = await ensure_user_profile(user_id, message.from_user, db_instance)
        if not user:
            await message.answer("Ошибка с профилем.", reply_markup=_get_back_to_menu_keyboard())
            await state.clear()
            return
        
        file_id = message.document.file_id
        file_name = message.document.file_name
        
        quest = await db_instance["quests"].find_one({"quest_id": quest_id})
        if not quest or quest.get("status") != "active":
            await message.answer(f"Квест с ID {quest_id} не активен.", reply_markup=_get_back_to_menu_keyboard())
            await state.clear()
            return
        
        creator_id = quest["creator_id"]
        creator = await ensure_user_profile(creator_id, message.from_user, db_instance)
        if not creator:
            await message.answer("Ошибка с создателем квеста.", reply_markup=_get_back_to_menu_keyboard())
            await state.clear()
            return
        
        preset_data = {
            "quest_id": quest_id,
            "user_id": user_id,
            "file_id": file_id,
            "file_name": file_name,
            "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "pending"
        }
        await db_instance["user_quests"].update_one(
            {"user_id": user_id, "quest_id": quest_id},
            {"$set": {"preset_submission": preset_data}},
            upsert=True
        )
        
        review_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Принять", callback_data=f"accept_preset_{quest_id}_{user_id}"),
             InlineKeyboardButton(text="Отклонить", callback_data=f"reject_preset_{quest_id}_{user_id}")]
        ])
        await message.bot.send_document(
            chat_id=creator_id,
            document=file_id,
            caption=f"Новый пресет для квеста <b>{quest['title']}</b> от @{message.from_user.username or message.from_user.first_name}:\nID: {quest_id}\nИмя файла: {file_name}",
            reply_markup=review_keyboard,
            parse_mode="HTML"
        )
        await message.answer(
            f"Ваш пресет для квеста <b>{quest['title']}</b> отправлен на проверку.",
            reply_markup=_get_back_to_menu_keyboard(),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Failed to process preset file for quest {quest_id}: {e}")
        await message.answer("Ошибка при обработке пресета.")
    await state.clear()

@quest_router.callback_query(F.data.startswith("accept_preset_"))
async def accept_preset(callback: CallbackQuery):
    logger.info(f"Creator {callback.from_user.id} accepted preset for quest: {callback.data}")
    db_instance = get_db()
    if db_instance is None or db_instance.name != DB_NAME:
        logger.error(f"Database is not initialized or incorrect DB name. Expected: {DB_NAME}")
        await callback.message.answer("Ошибка: база данных не инициализирована.")
        return
    full_data = callback.data.split("accept_preset_")[1]
    quest_id, user_id = full_data.rsplit("_", 1)
    user_id = int(user_id)
    
    try:
        quest = await db_instance["quests"].find_one({"quest_id": quest_id})
        if not quest or quest.get("status") != "active":
            await callback.message.answer(f"Квест с ID {quest_id} не активен.", reply_markup=_get_back_to_menu_keyboard())
            await callback.answer()
            return
        
        preset_submission = await db_instance["user_quests"].find_one({"user_id": user_id, "quest_id": quest_id})
        if not preset_submission or "preset_submission" not in preset_submission or preset_submission["preset_submission"]["status"] != "pending":
            await callback.message.answer("Пресет не найден или уже обработан.", reply_markup=_get_back_to_menu_keyboard())
            await callback.answer()
            return
        
        user = await ensure_user_profile(user_id, callback.from_user, db_instance)
        if not user:
            await callback.message.answer("Пользователь не найден.", reply_markup=_get_back_to_menu_keyboard())
            await callback.answer()
            return
        
        creator = await ensure_user_profile(int(callback.from_user.id), callback.from_user, db_instance)
        if not creator:
            await callback.message.answer("Ошибка с профилем создателя.", reply_markup=_get_back_to_menu_keyboard())
            await callback.answer()
            return
        
        reward = quest["reward"]
        new_balance = user["balance"] + reward
        avg_rating = preset_submission["preset_submission"].get("avg_rating", 0)
        if avg_rating >= 4:
            new_balance += 5
        
        await db_instance["user_profile"].update_one(
            {"user_id": user_id},
            {"$set": {"balance": new_balance, "quests_completed": user["quests_completed"] + 1}}
        )
        await db_instance["user_quests"].update_one(
            {"user_id": user_id, "quest_id": quest_id},
            {"$set": {"completed": True, "completed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "preset_submission.status": "accepted"}}
        )
        await db_instance["quests"].update_one(
            {"quest_id": quest_id},
            {"$set": {"status": "completed"}}
        )
        
        chat_id = callback.message.chat.id
        text = f"Пресет для квеста <b>{quest['title']}</b> принят. Начислено {reward} коинов."
        if chat_id in message_id_storage:
            try:
                await callback.message.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id_storage[chat_id],
                    text=text,
                    reply_markup=_get_back_to_menu_keyboard(),
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.warning(f"Failed to edit message {message_id_storage[chat_id]}: {e}")
                msg = await callback.message.answer(text, reply_markup=_get_back_to_menu_keyboard(), parse_mode="HTML")
                message_id_storage[chat_id] = msg.message_id
        else:
            msg = await callback.message.answer(text, reply_markup=_get_back_to_menu_keyboard(), parse_mode="HTML")
            message_id_storage[chat_id] = msg.message_id
        
        await callback.bot.send_message(
            chat_id=user_id,
            text=f"Ваш пресет для квеста <b>{quest['title']}</b> принят! Начислено {reward} коинов. Баланс: {new_balance}",
            reply_markup=_get_back_to_menu_keyboard(),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Failed to accept preset for quest {quest_id}: {e}")
        await callback.message.answer("Ошибка при принятии пресета.")
    await callback.answer()

@quest_router.callback_query(F.data.startswith("reject_preset_"))
async def reject_preset(callback: CallbackQuery):
    logger.info(f"Creator {callback.from_user.id} rejected preset for quest: {callback.data}")
    db_instance = get_db()
    if db_instance is None or db_instance.name != DB_NAME:
        logger.error(f"Database is not initialized or incorrect DB name. Expected: {DB_NAME}")
        await callback.message.answer("Ошибка: база данных не инициализирована.")
        return
    full_data = callback.data.split("reject_preset_")[1]
    quest_id, user_id = full_data.rsplit("_", 1)
    user_id = int(user_id)
    
    try:
        quest = await db_instance["quests"].find_one({"quest_id": quest_id})
        if not quest or quest.get("status") != "active":
            await callback.message.answer(f"Квест с ID {quest_id} не активен.", reply_markup=_get_back_to_menu_keyboard())
            await callback.answer()
            return
        
        preset_submission = await db_instance["user_quests"].find_one({"user_id": user_id, "quest_id": quest_id})
        if not preset_submission or "preset_submission" not in preset_submission or preset_submission["preset_submission"]["status"] != "pending":
            await callback.message.answer("Пресет не найден или уже обработан.", reply_markup=_get_back_to_menu_keyboard())
            await callback.answer()
            return
        
        user = await ensure_user_profile(user_id, callback.from_user, db_instance)
        if not user:
            await callback.message.answer("Пользователь не найден.", reply_markup=_get_back_to_menu_keyboard())
            await callback.answer()
            return
        
        creator = await ensure_user_profile(int(callback.from_user.id), callback.from_user, db_instance)
        if not creator:
            await callback.message.answer("Ошибка с профилем создателя.", reply_markup=_get_back_to_menu_keyboard())
            await callback.answer()
            return
        
        new_balance = max(0, user["balance"] - 10)
        await db_instance["user_profile"].update_one(
            {"user_id": user_id},
            {"$set": {"balance": new_balance}}
        )
        await db_instance["user_quests"].update_one(
            {"user_id": user_id, "quest_id": quest_id},
            {"$set": {"preset_submission.status": "rejected"}}
        )
        
        chat_id = callback.message.chat.id
        text = f"Пресет для квеста <b>{quest['title']}</b> отклонен."
        if chat_id in message_id_storage:
            try:
                await callback.message.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id_storage[chat_id],
                    text=text,
                    reply_markup=_get_back_to_menu_keyboard(),
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.warning(f"Failed to edit message {message_id_storage[chat_id]}: {e}")
                msg = await callback.message.answer(text, reply_markup=_get_back_to_menu_keyboard(), parse_mode="HTML")
                message_id_storage[chat_id] = msg.message_id
        else:
            msg = await callback.message.answer(text, reply_markup=_get_back_to_menu_keyboard(), parse_mode="HTML")
            message_id_storage[chat_id] = msg.message_id
        
        await callback.bot.send_message(
            chat_id=user_id,
            text=f"Ваш пресет для квеста <b>{quest['title']}</b> отклонен. Штраф: 10 коинов. Баланс: {new_balance}",
            reply_markup=_get_back_to_menu_keyboard(),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Failed to reject preset for quest {quest_id}: {e}")
        await callback.message.answer("Ошибка при отклонении пресета.")
    await callback.answer()

@quest_router.callback_query(F.data.startswith("accept_quest_"))
async def accept_quest(callback: CallbackQuery):
    logger.info(f"User {callback.from_user.id} attempting to accept quest: {callback.data}")
    db_instance = get_db()
    if db_instance is None or db_instance.name != DB_NAME:
        logger.error(f"Database is not initialized or incorrect DB name. Expected: {DB_NAME}")
        await callback.message.answer("Ошибка: база данных не инициализирована.")
        return
    quest_id = "_".join(callback.data.split("_")[2:])
    user_id = int(callback.from_user.id)

    try:
        user = await ensure_user_profile(user_id, callback.from_user, db_instance)
        if not user:
            await callback.message.answer("Ошибка с профилем.", reply_markup=_get_back_to_menu_keyboard())
            await callback.answer()
            return

        quest = await db_instance["quests"].find_one({"quest_id": quest_id, "status": "active"})
        if not quest:
            await callback.message.answer(f"Квест с ID {quest_id} не найден или завершен.", reply_markup=_get_back_to_menu_keyboard())
            await callback.answer()
            return

        user_quest = await db_instance["user_quests"].find_one({"user_id": user_id, "quest_id": quest_id})
        if user_quest:
            await callback.message.answer("Вы уже приняли этот квест.", reply_markup=_get_back_to_menu_keyboard())
            await callback.answer()
            return

        user_quest_data = {
            "user_id": user_id,
            "quest_id": quest_id,
            "accepted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "completed": False
        }
        await db_instance["user_quests"].insert_one(user_quest_data)
        
        await callback.message.answer(
            f"Вы приняли квест <b>{quest.get('title', 'Нет названия')}</b>!",
            reply_markup=_get_back_to_menu_keyboard(),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Failed to accept quest {quest_id} for user {user_id}: {e}")
        await callback.message.answer("Ошибка при принятии квеста.")
    await callback.answer()

async def list_quests(message: Message, is_my_quests: bool, user_id: int, db_instance=None):
    if db_instance is None:
        db_instance = get_db()
    if db_instance is None or db_instance.name != DB_NAME:
        logger.error(f"Database is not initialized or incorrect DB name. Expected: {DB_NAME}")
        await message.answer("Ошибка: база данных не инициализирована.", reply_markup=_get_back_to_menu_keyboard())
        return
    query = {"creator_id": user_id, "status": "active"} if is_my_quests else {"status": "active"}
    quests_collection = db_instance["quests"]
    try:
        quests = await quests_collection.find(query).sort("created_at", -1).to_list(length=None)
        if not quests:
            await message.answer("На данный момент квестов нет.", reply_markup=_get_back_to_menu_keyboard())
            return
        page = 0
        quests_per_page = 5
        total_pages = (len(quests) + quests_per_page - 1) // quests_per_page
        await send_quests_page(message, quests, page, total_pages, is_my_quests, user_id, db_instance)
    except Exception as e:
        logger.error(f"Database error while querying quests for user {user_id}: {e}")
        await message.answer("Ошибка при загрузке квестов.", reply_markup=_get_back_to_menu_keyboard())

async def send_quests_page(message: Message, quests, page: int, total_pages: int, is_my_quests: bool, user_id: int, db_instance):
    quests_per_page = 5
    start_index = page * quests_per_page
    end_index = min(start_index + quests_per_page, len(quests))
    page_quests = quests[start_index:end_index]
    
    quests_text = "\n\n".join([ 
        f"<b>{quest.get('title', 'Нет названия')}</b>\n"
        f"ID: {quest['quest_id']}\n"
        f"Категория: {quest.get('category', 'Нет категории')}\n"
        f"Описание: {quest.get('description', 'Нет описания')}\n"
        f"Награда: {quest.get('reward', 'Нет награды')} коинов"
        for quest in page_quests
    ])
    
    keyboard = stats_keyboard(page, total_pages, page_quests, is_my_quests, user_id)
    await message.answer(
        f"{'Ваши квесты:' if is_my_quests else 'Доступные квесты:'}\n\n{quests_text}",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

def stats_keyboard(page: int, total_pages: int, quests, is_my_quests: bool, user_id: int):
    buttons = []
    if page > 0:
        buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"quests_page:{page - 1}:{is_my_quests}"))
    if page < total_pages - 1:
        buttons.append(InlineKeyboardButton(text="➡️ Вперед", callback_data=f"quests_page:{page + 1}:{is_my_quests}"))
    if quests:
        for quest in quests:
            if is_my_quests:
                buttons.append(InlineKeyboardButton(text=f"Просмотреть пресеты для {quest['title']}", callback_data=f"view_presets_{quest['quest_id']}"))
            elif quest.get('status') == "active":
                buttons.append(InlineKeyboardButton(text=f"Принять {quest['title']}", callback_data=f"accept_quest_{quest['quest_id']}"))
    return InlineKeyboardMarkup(inline_keyboard=[buttons] if buttons else [])

@quest_router.callback_query(F.data.startswith("quests_page:"))
async def handle_quests_page(callback: CallbackQuery):
    db_instance = get_db()
    if db_instance is None or db_instance.name != DB_NAME:
        logger.error(f"Database is not initialized or incorrect DB name. Expected: {DB_NAME}")
        await callback.message.answer("Ошибка: база данных не инициализирована.")
        return
    data = callback.data.split(":")
    page = int(data[1])
    is_my_quests = data[2] == "True"
    user_id = int(callback.from_user.id)
    try:
        await ensure_user_profile(user_id, callback.from_user, db_instance)
        await list_quests(callback.message, is_my_quests, user_id, db_instance)
    except Exception as e:
        logger.error(f"Failed to handle quests page for user {user_id}: {e}")
        await callback.message.answer("Ошибка при переключении страницы квестов.")
    await callback.answer()

class ViewPresetsFilter(Filter):
    async def __call__(self, callback: CallbackQuery):
        return callback.data.startswith("view_presets_")

@quest_router.callback_query(ViewPresetsFilter())
async def view_presets(callback: CallbackQuery):
    db_instance = get_db()
    if db_instance is None or db_instance.name != DB_NAME:
        logger.error(f"Database is not initialized or incorrect DB name. Expected: {DB_NAME}")
        await callback.message.answer("Ошибка: база данных не инициализирована.")
        return
    quest_id = callback.data.split("view_presets_")[1]
    user_id = int(callback.from_user.id)

    try:
        quest = await db_instance["quests"].find_one({"quest_id": quest_id, "creator_id": user_id})
        if not quest:
            await callback.message.answer("Квест не найден или вы не его создатель.", reply_markup=_get_back_to_menu_keyboard())
            await callback.answer()
            return

        user_quests_collection = db_instance["user_quests"]
        presets = await user_quests_collection.find({"quest_id": quest_id, "preset_submission": {"$exists": True}}).to_list(length=None)
        if not presets:
            await callback.message.answer("Для этого квеста нет пресетов.", reply_markup=_get_back_to_menu_keyboard())
            await callback.answer()
            return

        presets_text = "\n\n".join([ 
            f"Пользователь: @{await get_username(preset['user_id'], db_instance)}\n"
            f"Статус: {preset['preset_submission']['status']}\n"
            f"Файл: {preset['preset_submission']['file_name']}"
            for preset in presets
        ])

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{'Принять' if preset['preset_submission']['status'] == 'pending' else 'Принято'}",
                    callback_data=f"accept_preset_{quest_id}_{preset['user_id']}" if preset['preset_submission']['status'] == 'pending' else "already_accepted"
                ),
                InlineKeyboardButton(
                    text=f"{'Отклонить' if preset['preset_submission']['status'] == 'pending' else 'Отклонено'}",
                    callback_data=f"reject_preset_{quest_id}_{preset['user_id']}" if preset['preset_submission']['status'] == 'pending' else "already_rejected"
                )
            ] for preset in presets
        ])
        keyboard.inline_keyboard.append([InlineKeyboardButton(text="Вернуться в меню", callback_data="back_to_menu")])
        await callback.message.answer(f"Пресеты для квеста <b>{quest['title']}</b>:\n\n{presets_text}", reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Failed to view presets for quest {quest_id}: {e}")
        await callback.message.answer("Ошибка при просмотре пресетов.")
    await callback.answer()

@quest_router.callback_query(F.data == "already_accepted")
async def already_accepted(callback: CallbackQuery):
    await callback.answer("Пресет уже принят.")

@quest_router.callback_query(F.data == "already_rejected")
async def already_rejected(callback: CallbackQuery):
    await callback.answer("Пресет уже отклонен.")