# ppsb>app>review
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from aiogram import Router
from aiogram.filters import Command
from datetime import datetime
from database import db

review_router = Router()

# Коллекция MongoDB
reviews_collection = db["reviews"]
active_users = set()

@review_router.message(Command("review"))
async def start_review(message: Message):
    if message.chat.type != "private":
        await message.answer("❌ Эта команда доступна только в личных сообщениях! Напишите мне в ЛС.")
        return
    user_id = message.from_user.id
    active_users.add(user_id)
    start_btn = InlineKeyboardButton(text="Начать отзыв", callback_data="start_review")
    cancel_btn = InlineKeyboardButton(text="Отмена", callback_data="cancel_review")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[start_btn, cancel_btn]])
    await message.answer("Что вы хотите сделать?", reply_markup=keyboard)

@review_router.callback_query(lambda c: c.data.startswith(("start_review", "cancel_review")))
async def handle_start_cancel(callback: CallbackQuery):
    user_id = callback.from_user.id
    if callback.data == "cancel_review":
        if user_id in active_users:
            active_users.remove(user_id)
        await callback.message.edit_text("❌ Написание отзыва отменено.")
        await callback.answer()
        return
    if callback.data == "start_review":
        agree_btn = InlineKeyboardButton(text="Согласен", callback_data="agree_terms")
        disagree_btn = InlineKeyboardButton(text="Не согласен", callback_data="disagree_terms")
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[agree_btn, disagree_btn]])
        await callback.message.edit_text("Для написания отзыва необходимо согласиться на обработку персональных данных.", reply_markup=keyboard)
        await callback.answer()

@review_router.callback_query(lambda c: c.data.startswith(("agree_terms", "disagree_terms")))
async def handle_agreement(callback: CallbackQuery):
    user_id = callback.from_user.id
    if callback.data == "disagree_terms":
        if user_id in active_users:
            active_users.remove(user_id)
        await callback.message.edit_text("❌ Вы не согласились на обработку данных. Написание отзыва отменено.")
        await callback.answer()
        return
    if callback.data == "agree_terms":
        await callback.message.edit_text("Пожалуйста, напишите ваш отзыв:")
        await callback.answer()

@review_router.message(lambda message: message.from_user.id in active_users and message.text)
async def process_feedback(message: Message):
    user_id = message.from_user.id
    data = {
        "user_id": message.from_user.id,
        "username": message.from_user.username,
        "name": message.from_user.first_name,
        "time": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
        "text": message.text
    }
    await reviews_collection.insert_one(data)
    active_users.remove(user_id)
    await message.answer("✅ Ваш отзыв успешно сохранён!")

@review_router.callback_query(lambda c: c.from_user.id in active_users)
async def handle_other_actions(callback: CallbackQuery):
    user_id = callback.from_user.id
    if user_id in active_users:
        active_users.remove(user_id)
    await callback.message.edit_text("❌ Написание отзыва отменено из-за несоответствующего действия.")
    await callback.answer()