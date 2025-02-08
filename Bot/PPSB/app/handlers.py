# ppsb>app>handlers
from aiogram import Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.filters import CommandStart, Command
from config import GITHUB, DONATE, WEBAPP_URL

router = Router()

@router.message(CommandStart())
async def start(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Создать квест 🎮", callback_data="create_quest")],
        [InlineKeyboardButton(text="Мои квесты 📋", callback_data="my_quests")],
        [InlineKeyboardButton(text="Профиль 👤", callback_data="profile")],
        [InlineKeyboardButton(text="Помощь 💡", callback_data="help")]
    ])
    await message.answer(
        "🎵 Добро пожаловать в мир звука и творчества! 🎵\n\n"
        "Здесь вы можете:\n"
        "✨ Создавать уникальные квесты для музыкантов.\n"
        "🎯 Участвовать в интересных заданиях.\n"
        "🎧 Загружать и делиться своими прессетами.\n"
        "📝 Оставлять отзывы и помогать развитию проекта.\n\n"
        "Выберите действие:",
        reply_markup=keyboard
    )

@router.message(Command('help'))
async def help_command(message: Message):
    await message.answer(
        "📚 Справка по использованию бота:\n\n"
        "/start – Главное меню.\n"
        "/help – Эта страница с подсказками.\n"
        "/github – Исходный код проекта на GitHub.\n"
        "/donate – Поддержите развитие проекта.\n"
        "/create_quest – Создайте новый квест.\n"
        "/profile – Просмотр вашего профиля.\n"
        "/quests – Начните выполнение доступных квестов.\n"
        "/upload_preset – Загрузите свой прессет.\n"
        "/review – Напишите отзыв о боте.\n\n"
        "🌟 Вместе мы создаем лучший инструмент для музыкантов!"
    )

@router.message(Command('github'))
async def github(message: Message):
    await message.answer(GITHUB)

@router.message(Command('donate'))
async def donate(message: Message):
    await message.answer(DONATE)

@router.message(Command('webapp'))
async def webapp(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Открыть Web App", web_app=WebAppInfo(url=WEBAPP_URL))]
    ])
    await message.answer(
        "Нажмите кнопку ниже, чтобы открыть Web App:",
        reply_markup=keyboard
    )