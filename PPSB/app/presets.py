from aiogram import Router, F
from aiogram.types import Message, Document, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from datetime import datetime
import logging
from config import DB_NAME
from database import get_db
from app.utils import message_id_storage  # Обновляем импорт

preset_router = Router()

class UploadPresetStates(StatesGroup):
    NAME = State()
    PLUGIN = State()
    DESCRIPTION = State()
    FILE = State()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    from app.handlers import back_to_menu_keyboard
    return back_to_menu_keyboard()

@preset_router.message(Command("upload_preset"))
async def start_upload_preset(message: Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} started uploading a new preset.")
    db_instance = get_db()
    if db_instance is None:
        logger.error(f"Database '{DB_NAME}' is not initialized. Cannot process /upload_preset command.")
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
    await state.set_state(UploadPresetStates.NAME)
    chat_id = message.chat.id
    text = "Шаг 1/4: Введите название пресета."
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

@preset_router.message(UploadPresetStates.NAME)
async def process_name(message: Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} entered name: {message.text}")
    name = message.text.strip()
    if not name:
        await message.answer("Название не может быть пустым. Попробуйте снова.")
        return
    await state.update_data(name=name)
    await message.answer("Шаг 2/4: Введите название плагина.")
    await state.set_state(UploadPresetStates.PLUGIN)

@preset_router.message(UploadPresetStates.PLUGIN)
async def process_plugin(message: Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} entered plugin: {message.text}")
    plugin = message.text.strip()
    if not plugin:
        await message.answer("Название плагина не может быть пустым. Попробуйте снова.")
        return
    await state.update_data(plugin=plugin)
    await message.answer("Шаг 3/4: Напишите описание пресета.")
    await state.set_state(UploadPresetStates.DESCRIPTION)

@preset_router.message(UploadPresetStates.DESCRIPTION)
async def process_description(message: Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} entered description: {message.text}")
    description = message.text.strip()
    if not description:
        await message.answer("Описание не может быть пустым. Попробуйте снова.")
        return
    await state.update_data(description=description)
    await message.answer("Шаг 4/4: Прикрепите файл с пресетом.")
    await state.set_state(UploadPresetStates.FILE)

@preset_router.message(UploadPresetStates.FILE, F.document)
async def process_file(message: Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} uploaded a file: {message.document.file_name}")
    db_instance = get_db()
    if db_instance is None:
        logger.error(f"Database '{DB_NAME}' is not initialized. Cannot process preset file.")
        await message.answer(f"Ошибка: база данных '{DB_NAME}' не инициализирована.")
        return
    presets_collection = db_instance["presets"]
    user_profile_collection = db_instance["user_profile"]
    file_id = message.document.file_id
    file_name = message.document.file_name
    data = await state.get_data()
    preset_name = data["name"]
    preset_data = {
        "name": preset_name,
        "plugin": data["plugin"],
        "description": data["description"],
        "category": data["plugin"],
        "file_id": file_id,
        "file_name": file_name,
        "creator_id": message.from_user.id,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "ratings": [],
        "avg_rating": 0
    }
    try:
        if await presets_collection.find_one({"name": preset_name}):
            await message.answer(f"Пресет с именем '{preset_name}' уже существует. Выберите другое имя.")
            return
        await presets_collection.insert_one(preset_data)
        user_id = message.from_user.id
        user = await user_profile_collection.find_one({"user_id": user_id})
        if user:
            new_presets = user["presets_uploaded"] + 1
            await user_profile_collection.update_one(
                {"user_id": user_id},
                {"$set": {"presets_uploaded": new_presets}}
            )
        await message.answer(f"Пресет '{preset_name}' загружен! Скачать: /download_preset {preset_name}")
    except Exception as e:
        logger.error(f"Failed to save preset for user {message.from_user.id}: {e}")
        await message.answer("Ошибка при сохранении пресета.")
    await state.clear()

@preset_router.message(Command("download_preset"))
async def download_preset(message: Message):
    logger.info(f"User {message.from_user.id} requested to download a preset: {message.text}")
    db_instance = get_db()
    if db_instance is None:
        logger.error(f"Database '{DB_NAME}' is not initialized. Cannot process /download_preset command.")
        await message.answer(f"Ошибка: база данных '{DB_NAME}' не инициализирована.")
        return
    presets_collection = db_instance["presets"]
    preset_name = message.text.split(maxsplit=1)[1].strip() if len(message.text.split()) > 1 else None
    if not preset_name:
        await message.answer("Укажите имя пресета: /download_preset MyPreset")
        return
    try:
        preset = await presets_collection.find_one({"name": preset_name})
        if not preset:
            await message.answer("Пресет не найден. Используйте /list_presets для списка.")
            return
        await message.answer_document(
            document=preset["file_id"],
            filename=preset["file_name"]
        )
    except Exception as e:
        logger.error(f"Error sending preset '{preset_name}': {e}")
        await message.answer("Ошибка при отправке пресета.")

@preset_router.message(Command("list_presets"))
async def list_presets(message: Message, db_instance=None):
    logger.info(f"User {message.from_user.id} requested list of presets.")
    if db_instance is None:
        db_instance = get_db()
    if db_instance is None:
        logger.error(f"Database '{DB_NAME}' is not initialized. Cannot process /list_presets command.")
        await message.answer(f"Ошибка: база данных '{DB_NAME}' не инициализирована.")
        return
    presets_collection = db_instance["presets"]
    try:
        presets = await presets_collection.find({}).sort("avg_rating", -1).to_list(length=None)
        if not presets:
            await message.answer("На данный момент нет пресетов.")
            return
        page = 0
        presets_per_page = 5
        total_pages = (len(presets) + presets_per_page - 1) // presets_per_page
        chat_id = message.chat.id
        await send_presets_page(message, presets, page, total_pages, chat_id)
    except Exception as e:
        logger.error(f"Failed to list presets: {e}")
        await message.answer("Ошибка при загрузке списка пресетов.")

async def send_presets_page(message: Message, presets, page: int, total_pages: int, chat_id: int):
    logger.info(f"Sending presets page {page} to user {message.from_user.id}")
    presets_per_page = 5
    start_index = page * presets_per_page
    end_index = start_index + presets_per_page
    page_presets = presets[start_index:end_index]
    
    presets_text = "\n".join([f"📄 {p['name']} (Рейтинг: {p.get('avg_rating', 0):.1f}, Плагин: {p['plugin']})" for p in page_presets])
    
    keyboard = presets_keyboard(page, total_pages, page_presets)
    if chat_id in message_id_storage:
        try:
            await message.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id_storage[chat_id],
                text=f"Доступные пресеты:\n\n{presets_text}",
                reply_markup=keyboard
            )
            return
        except Exception as e:
            logger.warning(f"Failed to edit message {message_id_storage[chat_id]}: {e}")
    msg = await message.answer(f"Доступные пресеты:\n\n{presets_text}", reply_markup=keyboard)
    if len(message_id_storage) > 1000:
        message_id_storage.clear()
    message_id_storage[chat_id] = msg.message_id

def presets_keyboard(page: int, total_pages: int, presets):
    buttons = []
    if page > 0:
        buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"presets_page:{page - 1}"))
    if page < total_pages - 1:
        buttons.append(InlineKeyboardButton(text="➡️ Вперед", callback_data=f"presets_page:{page + 1}"))
    for preset in presets:
        buttons.append(InlineKeyboardButton(text=f"Скачать {preset['name']}", callback_data=f"download_{preset['name']}"))
        buttons.append(InlineKeyboardButton(text=f"Оценить {preset['name']}", callback_data=f"rate_{preset['name']}"))
    return InlineKeyboardMarkup(inline_keyboard=[buttons] if buttons else [])

@preset_router.callback_query(F.data.startswith("presets_page:"))
async def handle_presets_page(callback: CallbackQuery):
    logger.info(f"User {callback.from_user.id} requested page {callback.data.split(':')[1]} of presets.")
    db_instance = get_db()
    if db_instance is None:
        logger.error(f"Database '{DB_NAME}' is not initialized. Cannot process presets page callback.")
        await callback.message.answer(f"Ошибка: база данных '{DB_NAME}' не инициализирована.")
        return
    presets_collection = db_instance["presets"]
    try:
        page = int(callback.data.split(":")[1])
        presets = await presets_collection.find({}).sort("avg_rating", -1).to_list(length=None)
        total_pages = (len(presets) + 4) // 5
        chat_id = callback.message.chat.id
        await send_presets_page(callback.message, presets, page, total_pages, chat_id)
    except Exception as e:
        logger.error(f"Failed to handle presets page: {e}")
        await callback.message.answer("Ошибка при загрузке страницы пресетов.")
    await callback.answer()

@preset_router.callback_query(F.data.startswith("download_"))
async def handle_download_preset_callback(callback: CallbackQuery):
    logger.info(f"User {callback.from_user.id} clicked to download preset: {callback.data}")
    db_instance = get_db()
    if db_instance is None:
        logger.error(f"Database '{DB_NAME}' is not initialized. Cannot process download preset callback.")
        await callback.message.answer(f"Ошибка: база данных '{DB_NAME}' не инициализирована.")
        return
    presets_collection = db_instance["presets"]
    preset_name = callback.data.split("download_")[1]
    try:
        preset = await presets_collection.find_one({"name": preset_name})
        if not preset:
            await callback.message.answer("Пресет не найден.")
            await callback.answer()
            return
        await callback.message.answer_document(
            document=preset["file_id"],
            filename=preset["file_name"]
        )
    except Exception as e:
        logger.error(f"Error sending preset '{preset_name}': {e}")
        await callback.message.answer("Ошибка при отправке пресета.")
    await callback.answer()

@preset_router.callback_query(F.data.startswith("rate_"))
async def handle_rate_preset_callback(callback: CallbackQuery, state: FSMContext):
    logger.info(f"User {callback.from_user.id} clicked to rate preset: {callback.data}")
    preset_name = callback.data.split("rate_")[1]
    await callback.message.answer(f"Введите рейтинг для {preset_name} (от 1 до 5):")
    await state.set_state("rating_preset")
    await state.update_data(preset_name=preset_name)
    await callback.answer()

@preset_router.message(F.text, lambda message: message.text.isdigit() and 1 <= int(message.text) <= 5)
async def process_rating(message: Message, state: FSMContext):
    if await state.get_state() != "rating_preset":
        return
    db_instance = get_db()
    if db_instance is None:
        logger.error(f"Database '{DB_NAME}' is not initialized. Cannot process rating.")
        await message.answer(f"Ошибка: база данных '{DB_NAME}' не инициализирована.")
        return
    presets_collection = db_instance["presets"]
    data = await state.get_data()
    preset_name = data.get("preset_name")
    if not preset_name:
        await message.answer("Ошибка. Попробуйте снова.")
        await state.clear()
        return
    
    try:
        preset = await presets_collection.find_one({"name": preset_name})
        if not preset:
            await message.answer("Пресет не найден.")
            await state.clear()
            return

        user_id = message.from_user.id
        rating = int(message.text)
        ratings = preset.get("ratings", [])
        if any(r["user_id"] == user_id for r in ratings):
            await message.answer("Вы уже оценили этот пресет.")
            await state.clear()
            return

        ratings.append({"user_id": user_id, "rating": rating})
        avg_rating = sum(r["rating"] for r in ratings) / len(ratings)
        await presets_collection.update_one(
            {"name": preset_name},
            {"$set": {"ratings": ratings, "avg_rating": avg_rating}}
        )
        await message.answer(f"Спасибо! Средний рейтинг {preset_name}: {avg_rating:.1f}")
    except Exception as e:
        logger.error(f"Failed to process rating for preset '{preset_name}': {e}")
        await message.answer("Ошибка при сохранении рейтинга.")
    await state.clear()