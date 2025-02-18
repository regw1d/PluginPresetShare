
---

# 🎵 PluginPresetShare Bot

Telegram-бот для музыкантов и звукорежиссеров, который помогает создавать и выполнять квесты, загружать прессеты для аудиоплагинов, а также оставлять отзывы. Бот разработан для удобного взаимодействия через инлайн-кнопки, что делает его использование максимально простым и интуитивно понятным.

---

## 🌟 Возможности

- **Создание квестов**: Создайте квест для других пользователей, указав жанр, вознаграждение и описание.
- **Выполнение квестов**: Выберите квест из списка и выполните его за 3 дня.
- **Загрузка прессетов**: Поделитесь своими прессетами для популярных аудиоплагинов (например, Serum, Massive, FabFilter).
- **Профиль пользователя**: Отслеживайте свои достижения, количество очков и рейтинг среди других пользователей.
- **Отзывы**: Оставьте отзыв о боте или проекте, чтобы помочь другим пользователям принять решение.

### Дополнительные возможности:
- **Интерактивное меню**: Используйте инлайн-кнопки для быстрого доступа к командам.
- **Уведомления**: Получайте напоминания о дедлайнах квестов.
- **Поддержка сообщества**: Общайтесь с другими музыкантами и звукорежиссерами через Telegram-канал.

---

## 🛠️ Технологии

- **Python**: Основной язык программирования.
- **aiogram**: Библиотека для создания Telegram-ботов.
- **FSM (Finite State Machine)**: Управление многошаговыми процессами (например, создание квеста или загрузка прессета).
- **JSON**: Хранение данных, таких как отзывы и профили пользователей.
- **InlineKeyboardMarkup**: Интерактивные кнопки для удобства использования.

---

## 📋 Команды

| Команда          | Описание                                                                 |
|------------------|-------------------------------------------------------------------------|
| `/start`         | Главное меню с интерактивными кнопками.                                 |
| `/help`          | Список доступных команд и инструкция по использованию бота.             |
| `/github`        | Ссылка на GitHub проекта.                                               |
| `/donate`        | Ссылка на страницу доната для поддержки разработки.                     |
| `/create_quest`  | Начало создания нового квеста.                                          |
| `/profile`       | Просмотр профиля пользователя.                                          |
| `/quest`         | Выбор и начало выполнения квеста.                                       |
| `/upload_preset` | Загрузка нового прессета для аудиоплагина.                              |
| `/review`        | Написание отзыва о боте или проекте.                                    |

---

## 🚀 Как начать

1. **Склонируйте репозиторий:**
   ```bash
   git clone https://github.com/regw1d/PluginPresetShare.git
   ```

2. **Установите зависимости:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Настройте токен бота в файле `config.py`:**
   ```python
   BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
   ```

4. **Запустите бота:**
   ```bash
   python main.py
   ```

---

## 📄 Лицензия

Этот проект распространяется под лицензией GNU GENERAL PUBLIC LICENSE. **Подробности см. в файле [LICENSE](LICENSE).**

---

## 🤝 Поддержка

Если вы хотите поддержать разработку проекта, воспользуйтесь одной из ссылок:

- [Boosty](https://boosty.to/regw1d)
- [Donation Alerts](https://www.donationalerts.com/r/regw1d)

---

## 📢 Контакты

- **Telegram Channel**: [Подпишитесь на наш канал](https://t.me/+2oWmBhIhLjw5OWI6) для новостей и обновлений.
- **GitHub**: [Репозиторий проекта](https://github.com/regw1d/PluginPresetShare)

---

## 📌 Основная информация

| Параметр                | Значение             |  
|-------------------------|----------------------|  
| 🗓️ Дата начала разработки | 22.01.2025         |  
| 📊 Текущий прогресс     | 25%                  |  
| ⏳ Дедлайн              | 15.02.2025           |  

### Разработчики:
- **[regw1d](https://github.com/regw1d/)** — основной разработчик кода.
- **[MaDeInCCCP](https://github.com/MaDeInCCCP2/)** — разработчик сайта.

---

## 💡 Как использовать кнопки?

После запуска бота (`/start`) вам будет предложено главное меню с инлайн-кнопками. Вот пример того, как это выглядит:

```
Главное меню:
[Создать квест] [Мой профиль]
[Выбрать квест] [Загрузить пресет]
[Оставить отзыв] [Помощь]
```

### Пример работы с кнопками:
1. **Создать квест**:
   - Нажмите кнопку "Создать квест".
   - Укажите жанр, вознаграждение и описание.
   - Квест будет опубликован для других пользователей.

2. **Выбрать квест**:
   - Нажмите кнопку "Выбрать квест".
   - Выберите интересующий вас квест из списка.
   - Выполните задание за 3 дня.

3. **Загрузить пресет**:
   - Нажмите кнопку "Загрузить пресет".
   - Прикрепите файл прессета и укажите название плагина.

4. **Оставить отзыв**:
   - Нажмите кнопку "Оставить отзыв".
   - Напишите текст отзыва, который будет сохранен в базе данных.

---

## 🔧 Планы на будущее

- **Добавление рейтинга**: Внедрение системы рейтинга для пользователей и квестов.
- **Интеграция с DAW**: Возможность экспорта прессетов напрямую из популярных DAW (например, FL Studio, Ableton Live).
- **Мультиязычность**: Поддержка нескольких языков для удобства международного сообщества.
- **Улучшение UI**: Добавление графических элементов и улучшение интерфейса.
