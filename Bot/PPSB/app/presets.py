# ppsb>app>presets
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from datetime import datetime
from database import db

preset_router = Router()

class UploadPresetStates(StatesGroup):
    NAME = State()
    PLUGIN = State()
    DESCRIPTION = State()
    QUEST = State()
    FILE = State()

# Коллекция MongoDB
presets_collection = db["presets"]

@preset_router.message(Command("upload_preset"))
async def start_upload_preset(message: Message, state: FSMContext):
    await message.answer("Вы начали загрузку нового прессета.\nШаг 1/5: Введите название прессета.")
    await state.set_state(UploadPresetStates.NAME)

@preset_router.message(UploadPresetStates.NAME)
async def process_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if not name:
        await message.answer("Название не может быть пустым. Попробуйте снова.")
        return
    await state.update_data(name=name)
    await message.answer("Шаг 2/5: Введите название плагина.")
    await state.set_state(UploadPresetStates.PLUGIN)

@preset_router.message(UploadPresetStates.PLUGIN)
async def process_plugin(message: Message, state: FSMContext):
    plugin = message.text.strip()
    if not plugin:
        await message.answer("Название плагина не может быть пустым. Попробуйте снова.")
        return
    await state.update_data(plugin=plugin)
    await message.answer("Шаг 3/5: Напишите описание прессета.")
    await state.set_state(UploadPresetStates.DESCRIPTION)

@preset_router.message(UploadPresetStates.DESCRIPTION)
async def process_description(message: Message, state: FSMContext):
    description = message.text.strip()
    if not description:
        await message.answer("Описание не может быть пустым. Попробуйте снова.")
        return
    await state.update_data(description=description)
    await message.answer("Шаг 4/5: Был ли этот прессет сделан по квесту? (Да/Нет)")
    await state.set_state(UploadPresetStates.QUEST)

@preset_router.message(UploadPresetStates.QUEST)
async def process_quest(message: Message, state: FSMContext):
    quest = message.text.strip().lower()
    if quest not in ["да", "нет"]:
        await message.answer("Ответ должен быть 'Да' или 'Нет'. Попробуйте снова.")
        return
    await state.update_data(quest=quest)
    await message.answer("Шаг 5/5: Прикрепите файл с прессетом.")
    await state.set_state(UploadPresetStates.FILE)

@preset_router.message(UploadPresetStates.FILE, F.document)
async def process_file(message: Message, state: FSMContext):
    file_id = message.document.file_id
    file_name = message.document.file_name
    data = await state.get_data()
    preset_name = f"Preset_{message.from_user.id}_{int(datetime.now().timestamp())}"
    preset_data = {
        "name": data["name"],
        "plugin": data["plugin"],
        "description": data["description"],
        "quest": data["quest"],
        "file_id": file_id,
        "file_name": file_name,
        "creator_id": message.from_user.id,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    await presets_collection.insert_one(preset_data)
    await message.answer(f"Прессет успешно загружен!")
    await state.clear()