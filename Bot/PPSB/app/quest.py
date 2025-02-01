from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from uuid import uuid4
from datetime import datetime
import random

quest_router = Router()

# FSM states
class QuestCreation(StatesGroup):
    TITLE = State()
    GENRE = State()
    DESCRIPTION = State()
    REWARD = State()
    ANSWER = State()

class QuestVerification(StatesGroup):
    ANSWER = State()

# Создание квеста
@quest_router.callback_query(F.data == "create_quest")
async def create_quest_start(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", callback_data="cancel_creation")
    msg = await callback.message.edit_text(
        "📝 Введите название квеста:",
        reply_markup=builder.as_markup()
    )
    await state.update_data(messages=[msg.message_id])
    await state.set_state(QuestCreation.TITLE)

# Обработка названия квеста
@quest_router.message(QuestCreation.TITLE)
async def process_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", callback_data="cancel_creation")
    msg = await message.answer(
        "🎭 Введите жанр квеста:",
        reply_markup=builder.as_markup()
    )
    data = await state.get_data()
    messages = data.get('messages', [])
    messages.append(msg.message_id)
    await state.update_data(messages=messages)
    await state.set_state(QuestCreation.GENRE)
    

# Класс для квеста
class Quest:
    def __init__(self, owner_id: int, title: str, genre: str, description: str, reward: int, answer: str):
        self.id = str(uuid4())  # ID квеста
        self.owner_id = owner_id  # ID создателя
        self.title = title  # Название квеста
        self.genre = genre  # Жанр квеста
        self.description = description  # Описание
        self.reward = reward  # Награда (10–100 очков)
        self.answer = answer  # Ответ
        self.created_at = datetime.now()  # Дата создания
        self.status = 'active'  # Статус: active/completed/canceled
        self.messages = []  # Сообщения с квестом
        self.attempts = {}  # Попытки ответов {user_id: {'chat_id': chat_id, 'message_id': message_id, 'answer': answer}}

# Класс для пользователя
class User:
    def __init__(self, user_id: int):
        self.user_id = user_id  # ID пользователя
        self.points = 100  # Очки
        self.reserved_points = 0  # Зарезервированные очки
        self.created_quests = []  # Созданные квесты
        self.completed_quests = []  # Завершенные квесты

# Глобальные переменные для хранения данных
users: dict[int, User] = {}  # Все пользователи {user_id: User}
quests: dict[str, Quest] = {}  # Все квесты {quest_id: Quest}

# Утилиты
def get_user(user_id: int) -> User:
    if user_id not in users:
        users[user_id] = User(user_id)
    return users[user_id]

# Главное меню
def main_menu() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Создать квест", callback_data="create_quest")
    builder.button(text="📜 Мои квесты", callback_data="my_quests")
    builder.button(text="🎲 Случайный квест", callback_data="random_quest")
    builder.button(text="💰 Баланс", callback_data="balance")
    builder.adjust(1)
    return builder

# Удаление всех сообщений квеста
async def delete_quest_messages(quest: Quest, bot: Bot):
    for msg in quest.messages:
        try:
            await bot.delete_message(chat_id=msg['chat_id'], message_id=msg['message_id'])
        except Exception:
            pass
    quest.messages.clear()

# Команда /quest
@quest_router.message(Command('quest'))
async def quest_handler(message: Message):
    await message.answer(
        "🎮 Добро пожаловать в систему квестов!",
        reply_markup=main_menu().as_markup()
    )

# Создание квеста
@quest_router.callback_query(F.data == "create_quest")
async def create_quest_start(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", callback_data="cancel_creation")
    msg = await callback.message.edit_text(
        "📝 Введите название квеста:",
        reply_markup=builder.as_markup()
    )
    await state.update_data(messages=[msg.message_id])
    await state.set_state(QuestCreation.TITLE)

# Обработка названия квеста
@quest_router.message(QuestCreation.TITLE)
async def process_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", callback_data="cancel_creation")
    msg = await message.answer(
        "🎭 Введите жанр квеста:",
        reply_markup=builder.as_markup()
    )
    data = await state.get_data()
    messages = data.get('messages', [])
    messages.append(msg.message_id)
    await state.update_data(messages=messages)
    await state.set_state(QuestCreation.GENRE)

# Обработка жанра квеста
@quest_router.message(QuestCreation.GENRE)
async def process_genre(message: Message, state: FSMContext):
    await state.update_data(genre=message.text)
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", callback_data="cancel_creation")
    msg = await message.answer(
        "📖 Введите описание квеста:",
        reply_markup=builder.as_markup()
    )
    data = await state.get_data()
    messages = data.get('messages', [])
    messages.append(msg.message_id)
    await state.update_data(messages=messages)
    await state.set_state(QuestCreation.DESCRIPTION)

# Обработка описания квеста
@quest_router.message(QuestCreation.DESCRIPTION)
async def process_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", callback_data="cancel_creation")
    msg = await message.answer(
        "💰 Укажите награду (10–100 очков):",
        reply_markup=builder.as_markup()
    )
    data = await state.get_data()
    messages = data.get('messages', [])
    messages.append(msg.message_id)
    await state.update_data(messages=messages)
    await state.set_state(QuestCreation.REWARD)

# Обработка награды квеста
@quest_router.message(QuestCreation.REWARD)
async def process_reward(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    try:
        reward = int(message.text)
        if not 10 <= reward <= 100:
            raise ValueError
        if reward > (user.points - user.reserved_points):
            await message.answer("❌ Недостаточно свободных очков!")
            return
    except ValueError:
        await message.answer("❌ Введите число от 10 до 100!")
        return
    user.reserved_points += reward
    await state.update_data(reward=reward)
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", callback_data="cancel_creation")
    msg = await message.answer(
        "📝 Введите задание или вопрос, на который вам могут ответить:",
        reply_markup=builder.as_markup()
    )
    data = await state.get_data()
    messages = data.get('messages', [])
    messages.append(msg.message_id)
    await state.update_data(messages=messages)
    await state.set_state(QuestCreation.ANSWER)

# Обработка ответа квеста
@quest_router.message(QuestCreation.ANSWER)
async def process_answer(message: Message, state: FSMContext, bot: Bot):
    user = get_user(message.from_user.id)
    data = await state.get_data()
    quest = Quest(
        owner_id=user.user_id,
        title=data['title'],
        genre=data['genre'],
        description=data['description'],
        reward=data['reward'],
        answer=message.text
    )
    user.reserved_points -= quest.reward
    quests[quest.id] = quest
    user.created_quests.append(quest.id)
    await message.answer(
        f"✅ Квест создан!\nНаграда: {quest.reward} очков",
        reply_markup=main_menu().as_markup()
    )
    await state.clear()

# Показ активных квестов
@quest_router.callback_query(F.data == "my_quests")
async def show_my_quests(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    builder = InlineKeyboardBuilder()
    for quest_id in user.created_quests:
        quest = quests.get(quest_id)
        if quest and quest.status == 'active':
            builder.button(
                text=f"❌ {quest.title} ({quest.reward} очков)",
                callback_data=f"cancel_{quest_id}"
            )
    builder.button(text="🔙 Назад", callback_data="main_menu")
    builder.adjust(1)
    await callback.message.edit_text(
        "📜 Ваши активные квесты:",
        reply_markup=builder.as_markup()
    )

# Отмена квеста
@quest_router.callback_query(F.data.startswith("cancel_"))
async def cancel_quest_handler(callback: CallbackQuery):
    quest_id = callback.data.split("_")[1]
    quest = quests.get(quest_id)
    if not quest:
        await callback.answer("❌ Квест не найден!", show_alert=True)
        return

    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подтвердить", callback_data=f"confirm_cancel_{quest_id}")
    builder.button(text="❌ Отмена", callback_data="my_quests")
    builder.adjust(2)

    await callback.message.edit_text(
        f"❗ Вернуть {quest.reward} очков и удалить квест?",
        reply_markup=builder.as_markup()
    )

# Подтверждение отмены квеста
@quest_router.callback_query(F.data.startswith("confirm_cancel_"))
async def confirm_cancel(callback: CallbackQuery, bot: Bot):
    quest_id = callback.data.split("_")[2]
    quest = quests.get(quest_id)
    user = get_user(callback.from_user.id)
    if quest and quest.status == 'active':
        user.reserved_points -= quest.reward
        user.points += quest.reward
        await delete_quest_messages(quest, bot)
        quest.status = 'canceled'
        user.created_quests.remove(quest_id)
        await callback.answer("✅ Квест отменен!", show_alert=True)
    else:
        await callback.answer("❌ Ошибка отмены!", show_alert=True)
    await callback.message.edit_text(
        "🎮 Главное меню:",
        reply_markup=main_menu().as_markup()
    )

# Получение случайного квеста
@quest_router.callback_query(F.data == "random_quest")
async def random_quest_handler(callback: CallbackQuery):
    active_quests = [q for q in quests.values() if q.status == 'active']
    if not active_quests:
        await callback.answer("😞 Нет доступных квестов", show_alert=True)
        return
    quest = random.choice(active_quests)
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Принять квест", callback_data=f"accept_{quest.id}")
    builder.button(text="🔙 Назад", callback_data="main_menu")
    msg = await callback.message.edit_text(
        f"🎯 Квест: {quest.title}\n"
        f"🎭 Жанр: {quest.genre}\n"
        f"📖 Описание: {quest.description}\n"
        f"💰 Награда: {quest.reward} очков",
        reply_markup=builder.as_markup()
    )
    quest.messages.append({'chat_id': msg.chat.id, 'message_id': msg.message_id})

# Принятие квеста
@quest_router.callback_query(F.data.startswith("accept_"))
async def accept_quest(callback: CallbackQuery, state: FSMContext):
    quest_id = callback.data.split("_")[1]
    quest = quests.get(quest_id)
    if quest and quest.status == 'active':
        await state.update_data(quest_id=quest_id)
        builder = InlineKeyboardBuilder()
        builder.button(text="❌ Отмена", callback_data="main_menu")
        msg = await callback.message.answer(
            "📝 Введите ваш ответ для подтверждения выполнения:",
            reply_markup=builder.as_markup()
        )
        quest.messages.append({'chat_id': msg.chat.id, 'message_id': msg.message_id})
        await state.set_state(QuestVerification.ANSWER)

# Проверка ответа на квест
@quest_router.message(QuestVerification.ANSWER)
async def verify_answer(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    quest_id = data.get('quest_id')
    quest = quests.get(quest_id)
    user = get_user(message.from_user.id)

    if not quest or quest.status != 'active':
        await message.answer("❌ Квест больше не доступен!")
        await state.clear()
        return

    # Проверяем, является ли пользователь автором квеста
    if user.user_id == quest.owner_id:
        await message.answer("❌ Вы не можете выполнить свой собственный квест!")
        await state.clear()
        return

    # Сохраняем попытку ответа
    quest.attempts[user.user_id] = {
        'chat_id': message.chat.id,
        'message_id': message.message_id,
        'answer': message.text
    }

    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подтвердить выполнение", callback_data=f"approve_{quest_id}_{user.user_id}")
    builder.button(text="❌ Отклонить выполнение", callback_data=f"reject_{quest_id}_{user.user_id}")
    builder.adjust(1)

    # Отправляем сообщение автору квеста
    await bot.send_message(
        quest.owner_id,
        f"👤 Пользователь {user.user_id} отправил ответ на квест '{quest.title}':\n"
        f"📝 Ответ: {message.text}\n\n"
        f"🔑 Правильный ответ: {quest.answer}",
        reply_markup=builder.as_markup()
    )

    await message.answer("⏳ Ваш ответ отправлен на проверку автору квеста")
    await state.clear()

# Подтверждение выполнения квеста
@quest_router.callback_query(F.data.startswith("approve_"))
async def approve_answer(callback: CallbackQuery, bot: Bot):
    _, quest_id, user_id = callback.data.split("_")
    quest = quests.get(quest_id)
    author = get_user(callback.from_user.id)
    user = get_user(int(user_id))

    if quest and quest.status == 'active' and quest.owner_id == author.user_id:
        # Увеличиваем баланс пользователя
        user.points += quest.reward
        # Уменьшаем зарезервированные очки автора
        author.reserved_points -= quest.reward
        # Добавляем квест в список завершенных
        user.completed_quests.append(quest_id)
        # Меняем статус квеста на "completed"
        quest.status = 'completed'
        # Удаляем сообщения квеста
        await delete_quest_messages(quest, bot)

        # Уведомляем пользователя о получении награды
        await bot.send_message(
            user.user_id,
            f"✅ Автор подтвердил ваш ответ! Получено {quest.reward} очков"
        )
        await callback.answer("✅ Выплата произведена!")

# Отклонение выполнения квеста
@quest_router.callback_query(F.data.startswith("reject_"))
async def reject_answer(callback: CallbackQuery, bot: Bot):
    _, quest_id, user_id = callback.data.split("_")
    quest = quests.get(quest_id)
    author = get_user(callback.from_user.id)
    user = get_user(int(user_id))
    if quest and quest.status == 'active' and quest.owner_id == author.user_id:
        await bot.send_message(user.user_id, "❌ Автор отклонил ваш ответ! Попробуйте еще раз")
        attempt = quest.attempts.get(user.user_id)
        if attempt:
            try:
                await bot.delete_message(attempt['chat_id'], attempt['message_id'])
            except Exception:
                pass
            del quest.attempts[user.user_id]
        await callback.answer("❌ Выполнение отклонено!")

# Показ баланса
@quest_router.callback_query(F.data == "balance")
async def show_balance(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    await callback.answer(
        f"💰 Ваш баланс: {user.points} очков",
        show_alert=True
    )

# Возврат в главное меню
@quest_router.callback_query(F.data == "main_menu")
async def back_to_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "🎮 Главное меню:",
        reply_markup=main_menu().as_markup()
    )

# Отмена создания квеста
@quest_router.callback_query(F.data == "cancel_creation")
async def cancel_creation(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user = get_user(callback.from_user.id)
    if 'reward' in data:
        user.points += data['reward']
        user.reserved_points -= data['reward']
    await state.clear()
    await callback.message.edit_text(
        "❌ Создание отменено",
        reply_markup=main_menu().as_markup()
    )
