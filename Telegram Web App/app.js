// Инициализация Telegram Web App
const tg = window.Telegram.WebApp;

// Показываем кнопку "Закрыть" в Telegram Web App
tg.expand(); // Раскрываем Web App на весь экран
tg.MainButton.show(); // Показываем основную кнопку
tg.MainButton.setText("Закрыть"); // Устанавливаем текст кнопки

// Обработчик для кнопки "Закрыть"
tg.MainButton.onClick(() => {
    tg.close(); // Закрываем Web App
});

// Получаем данные пользователя
const user = tg.initDataUnsafe.user;

if (user) {
    console.log("Данные пользователя:", user);
    // Пример: Отображаем имя пользователя
    const userName = user.first_name || "Пользователь";
    document.getElementById('user-name').textContent = `Привет, ${userName}!`;
}

// Инициализация баланса (только на главной странице)
let balance = parseInt(localStorage.getItem('userBalance')) || 100; // Начальный баланс
const balanceElement = document.getElementById('balanceAmount');

// Инициализация темы
const themeToggle = document.createElement('button');
themeToggle.textContent = '🌙';
themeToggle.classList.add('btn', 'btn-primary');
themeToggle.style.position = 'fixed';
themeToggle.style.top = '1rem';
themeToggle.style.right = '1rem';
themeToggle.style.zIndex = '1000';
document.body.appendChild(themeToggle);

// Функция для обновления баланса
function updateBalance(amount) {
    balance += amount;
    if (balanceElement) {
        balanceElement.textContent = `${balance} CP`;
    }
    localStorage.setItem('userBalance', balance); // Сохраняем баланс
}

// Функция для загрузки баланса
function loadBalance() {
    const savedBalance = localStorage.getItem('userBalance');
    if (savedBalance) {
        balance = parseInt(savedBalance, 10);
    }
    if (balanceElement) {
        balanceElement.textContent = `${balance} CP`;
    }
}

// Функция для смены темы
function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme); // Сохраняем тему
    themeToggle.textContent = newTheme === 'dark' ? '☀️' : '🌙';
}

// Функция для применения темы
function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    themeToggle.textContent = theme === 'dark' ? '☀️' : '🌙';
}

// Загрузка темы
function loadTheme() {
    // Синхронизация с темой Telegram
    const telegramTheme = tg.colorScheme; // Получаем тему Telegram
    const savedTheme = localStorage.getItem('theme') || telegramTheme; // Используем тему Telegram по умолчанию
    applyTheme(savedTheme); // Применяем тему
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    loadBalance();
    loadTheme();

    themeToggle.addEventListener('click', toggleTheme);

    // Пример: Добавление CP за активность
    setTimeout(() => {
        updateBalance(10);
        alert('+10 CP за активность!');
    }, 60000); // Через 1 минуту
});

// Поиск пресетов
const searchInput = document.createElement('input');
searchInput.placeholder = 'Поиск пресетов...';
searchInput.classList.add('form-input');
document.querySelector('.search-bar')?.appendChild(searchInput);

searchInput.addEventListener('input', (e) => {
    const searchTerm = e.target.value.toLowerCase();
    const presets = document.querySelectorAll('.preset-card');
    presets.forEach(preset => {
        const title = preset.querySelector('h3').textContent.toLowerCase();
        if (title.includes(searchTerm)) {
            preset.style.display = 'block';
        } else {
            preset.style.display = 'none';
        }
    });
});

// Топ-10 пресетов по популярности
const topPresets = [
    { name: 'Preset 1', description: 'Описание пресета 1', popularity: 100 },
    { name: 'Preset 2', description: 'Описание пресета 2', popularity: 90 },
    // Добавьте больше пресетов
];

const topPresetsList = document.createElement('div');
topPresetsList.classList.add('presets-list');
document.querySelector('.section')?.appendChild(topPresetsList);

topPresets.forEach(preset => {
    const presetCard = document.createElement('div');
    presetCard.classList.add('preset-card');
    presetCard.innerHTML = `
        <h3>${preset.name}</h3>
        <p>${preset.description}</p>
        <p>Популярность: ${preset.popularity}</p>
    `;
    topPresetsList.appendChild(presetCard);
});

// Достижения (только на главной странице)
if (document.getElementById('achievements-section')) {
    const achievements = [
        { name: 'Новичок', description: 'Загрузите первый пресет', completed: false },
        { name: 'Энтузиаст', description: 'Загрузите 5 пресетов', completed: false },
        // Добавьте больше достижений
    ];

    const achievementsSection = document.getElementById('achievements-section');
    achievementsSection.innerHTML = ''; // Очищаем содержимое

    achievements.forEach(achievement => {
        const achievementCard = document.createElement('div');
        achievementCard.classList.add('achievement-card');
        achievementCard.innerHTML = `
            <h3>${achievement.name}</h3>
            <p>${achievement.description}</p>
            <p>${achievement.completed ? '✅ Выполнено' : '❌ Не выполнено'}</p>
        `;
        achievementsSection.appendChild(achievementCard);
    });
}

// Награда за загрузку пресетов
document.getElementById('upload-preset-form')?.addEventListener('submit', (e) => {
    e.preventDefault();
    updateBalance(10);
    alert('+10 CP за загрузку пресета!');
});

// Создание квеста
document.getElementById('create-quest-form')?.addEventListener('submit', (e) => {
    e.preventDefault();
    const reward = parseInt(document.querySelector('#create-quest-form input[type="number"]').value, 10);
    if (deductBalance(reward)) {
        alert(`Квест создан! С вашего баланса списано ${reward} CP.`);
    }
});
