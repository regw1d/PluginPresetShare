# ppsb>app>quests
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from datetime import datetime, timedelta
import asyncio
from database import db

quest_router = Router()

class CreateQuestStates(StatesGroup):
    GENRE = State()
    REWARD = State()
    DESCRIPTION = State()

# Коллекции MongoDB
quests_collection = db["quests"]
user_profiles_collection = db["user_profiles"]
quest_timers_collection = db["quest_timers"]

async def check_quest_timers(bot):
    while True:
        current_time = datetime.now()
        async for timer in quest_timers_collection.find():
            user_id = timer["user_id"]
            quest_name = timer["quest_name"]
            end_time = timer["end_time"]
            if current_time >= end_time:
                user_profile = await user_profiles_collection.find_one({"user_id": user_id})
                if user_profile and user_profile.get("current_quest") == quest_name:
                    await user_profiles_collection.update_one(
                        {"user_id": user_id},
                        {
                            "$push": {"completed_quests": quest_name},
                            "$inc": {"points": quests_collection.find_one({"name": quest_name})["reward"]},
                            "$unset": {"current_quest": ""}
                        }
                    )
                    await quest_timers_collection.delete_one({"user_id": user_id})
                    await bot.send_message(user_id, f"🎉 Поздравляем! Ваш квест '{quest_name}' был автоматически принят после истечения времени.")
        await asyncio.sleep(60)

@quest_router.message(Command("create_quest"))
async def start_create_quest(message: Message, state: FSMContext):
    await message.answer("Вы начали создание нового квеста.\nШаг 1/3: Введите жанр прессета (например, 'Future Bass', 'EDM').")
    await state.set_state(CreateQuestStates.GENRE)

@quest_router.message(CreateQuestStates.GENRE)
async def process_genre(message: Message, state: FSMContext):
    genre = message.text.strip()
    if not genre:
        await message.answer("Жанр не может быть пустым. Попробуйте снова.")
        return
    await state.update_data(genre=genre)
    await message.answer("Шаг 2/3: Укажите сумму вознаграждения (от 10 до 100).")
    await state.set_state(CreateQuestStates.REWARD)

@quest_router.message(CreateQuestStates.REWARD)
async def process_reward(message: Message, state: FSMContext):
    try:
        reward = int(message.text.strip())
        if reward < 10 or reward > 100:
            raise ValueError()
    except ValueError:
        await message.answer("Сумма должна быть целым числом от 10 до 100. Попробуйте снова.")
        return
    await state.update_data(reward=reward)
    await message.answer("Шаг 3/3: Напишите описание квеста (например, 'Создайте прессет для плагина Massive').")
    await state.set_state(CreateQuestStates.DESCRIPTION)

@quest_router.message(CreateQuestStates.DESCRIPTION)
async def process_description(message: Message, state: FSMContext):
    description = message.text.strip()
    if not description:
        await message.answer("Описание не может быть пустым. Попробуйте снова.")
        return
    data = await state.get_data()
    quest_name = f"CustomQuest_{message.from_user.id}_{int(datetime.now().timestamp())}"
    quest_data = {
        "name": quest_name,
        "genre": data["genre"],
        "reward": data["reward"],
        "description": description,
        "creator_id": message.from_user.id,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    await quests_collection.insert_one(quest_data)
    await message.answer(f"Квест успешно создан!")
    await state.clear()

@quest_router.message(Command("profile"))
async def show_profile(message: Message):
    user_id = message.from_user.id
    user_profile = await user_profiles_collection.find_one({"user_id": user_id})
    if not user_profile:
        user_profile = {
            "user_id": user_id,
            "username": message.from_user.username,
            "first_name": message.from_user.first_name,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "completed_quests": [],
            "points": 0
        }
        await user_profiles_collection.insert_one(user_profile)
    completed_quests = len(user_profile.get("completed_quests", []))
    points = user_profile.get("points", 0)
    await message.answer(
        f"👤 Профиль пользователя:\n\n"
        f"📝 Имя: {user_profile['first_name']}\n"
        f"🔢 ID: {user_id}\n"
        f"✅ Завершено квестов: {completed_quests}\n"
        f"⭐ Очки: {points}"
    )

@quest_router.message(Command("quests"))
async def start_quest(message: Message):
    user_id = message.from_user.id
    user_profile = await user_profiles_collection.find_one({"user_id": user_id})
    if not user_profile:
        user_profile = {
            "user_id": user_id,
            "current_quest": None,
            "completed_quests": [],
            "progress": {}
        }
        await user_profiles_collection.insert_one(user_profile)
    available_quests = [
        quest async for quest in quests_collection.find({"creator_id": {"$ne": user_id}, "name": {"$nin": user_profile["completed_quests"]}})
    ]
    if not available_quests:
        await message.answer("❌ В данный момент квесты недоступны.")
        return
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=quest["name"], callback_data=f"start_quest:{quest['name']}")]
            for quest in available_quests
        ]
    )
    await message.answer(
        "Выберите квест, который хотите начать:",
        reply_markup=keyboard
    )

@quest_router.callback_query(F.data.startswith("start_quest:"))
async def handle_start_quest(callback: CallbackQuery):
    quest_name = callback.data.split(":")[1]
    user_id = callback.from_user.id
    user_profile = await user_profiles_collection.find_one({"user_id": user_id})
    if quest_name in user_profile.get("completed_quests", []):
        await callback.answer("Вы уже завершили этот квест!", show_alert=True)
        return
    await user_profiles_collection.update_one({"user_id": user_id}, {"$set": {"current_quest": quest_name}})
    end_time = datetime.now() + timedelta(days=3)
    await quest_timers_collection.insert_one({"user_id": user_id, "quest_name": quest_name, "end_time": end_time})
    await callback.message.edit_text(f"Вы начали квест: {quest_name}. У вас есть 3 дня на выполнение.")
    await callback.answer()

async def start_check_quest_timers(bot):
    asyncio.create_task(check_quest_timers(bot))