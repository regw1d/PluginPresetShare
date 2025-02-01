# contact.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import Message
from datetime import datetime
from config import *
import json
import os

contact_router = Router()

# Путь к файлу для хранения отзывов
JSON_FILE = "contact.json"
active_sessions = set()

# Функция для сохранения отзыва
def save_review(user: types.User, review_text: str):
    review_data = {
        "user_id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "review_text": review_text,
        "timestamp": datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    }
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = {"contact": []}
    data["contact"].append(review_data)
    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Команда /contact
@contact_router.message(Command("contact"))
async def start_review(message: types.Message):
    # Проверяем, является ли чат личным сообщением
    if message.chat.type != "private":
        await message.answer("❌ Только в ЛС!")
        return

    user_id = message.from_user.id
    active_sessions.add(user_id)
    cancel_btn = InlineKeyboardButton(text="Отмена", callback_data="cancel_review")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[cancel_btn]])
    await message.answer("Оставьте отзыв:", reply_markup=keyboard)

# Отмена отзыва
@contact_router.callback_query(lambda c: c.data == "cancel_review")
async def cancel_review(callback: CallbackQuery):
    user_id = callback.from_user.id
    if user_id in active_sessions:
        active_sessions.remove(user_id)
    await callback.message.edit_text("❌ Отзыв отменён")
    await callback.answer()

# Обработка текста отзыва
@contact_router.message()
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    if user_id not in active_sessions:
        return

    # Сохраняем отзыв
    save_review(message.from_user, message.text)
    active_sessions.remove(user_id)
    await message.answer("✅ Отзыв успешно сохранён!")
