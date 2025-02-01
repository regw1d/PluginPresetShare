# handlers.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram import Router, types
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from datetime import datetime
from config import GITHUB, DONATE

router = Router()

@router.message(CommandStart())
async def start(message: Message):
    await message.answer(
        'PluginPresetsShareBot (PPSB) is already work! For start work with bot send /quest'
    )

@router.message(Command('help'))
async def help_command(message: Message):
    await message.answer(
        "Доступные команды бота:\n"
        "/start – Просто тест команда.\n"
        "/help – Страница с подсказками.\n"
        "/github – Ссылка на github проекта.\n"
        "/donate – Поддержать автора.\n"
        "/contact – Написать отзыв.\n"
        "/quest – Основная команда бота (МНОГО БАГОВ!).\n"
    )

@router.message(Command('github'))
async def github(message: Message):
    await message.answer(GITHUB)

@router.message(Command('donate'))
async def donate(message: Message):
    await message.answer(DONATE)
