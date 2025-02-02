const tg = window.Telegram.WebApp;
tg.expand();
tg.MainButton.setText("Закрыть").onClick(() => tg.close()).show();

// Инициализация данных пользователя
const userData = tg.initDataUnsafe;
const userId = userData?.user?.id || "guest";
let balance = 100;

// Синхронизация данных с Telegram
function syncWithTelegram() {
    tg.CloudStorage.setItem("userBalance", balance.toString(), (err) => {
        if (err) console.error("Ошибка синхронизации баланса:", err);
    });
}

// Обновление баланса
async function updateBalance(amount) {
    balance += amount;
    try {
        await fetch('https://your-server.com/update-balance', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Telegram-User-ID': userId,
            },
            body: JSON.stringify({ balance }),
        });
        syncWithTelegram();
        tg.showPopup({ title: 'Успех!', message: `Баланс: ${balance} CP`, buttons: [{ type: 'close' }] });
    } catch (error) {
        tg.showAlert("Ошибка синхронизации баланса");
    }
}

// Загрузка пресетов
document.getElementById('upload-preset-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const file = document.getElementById('presetFile').files[0];
    if (file.size > 2 * 1024 * 1024) {
        tg.showAlert("Файл не должен превышать 2 МБ");
        return;
    }

    const preset = {
        id: Date.now().toString(),
        name: document.getElementById('presetName').value,
        description: document.getElementById('presetDescription').value,
        file: file.name,
        likes: 0,
        comments: []
    };

    presets.push(preset);
    localStorage.setItem('presets', JSON.stringify(presets));
    tg.showAlert("Пресет загружен!");
    updateBalance(10);
    window.location.href = `preset.html?id=${preset.id}`; // Переход на страницу пресета
});

// Создание квестов
document.getElementById('create-quest-form').addEventListener('submit', (e) => {
    e.preventDefault();
    const quest = {
        id: Date.now().toString(),
        name: document.getElementById('questName').value,
        description: document.getElementById('questDescription').value,
        reward: parseInt(document.getElementById('questReward').value, 10),
        completed: false
    };

    quests.push(quest);
    localStorage.setItem('quests', JSON.stringify(quests));
    tg.showAlert("Квест создан!");
    renderQuests();
});

// Рендер квестов
function renderQuests() {
    const questsList = document.getElementById('quests-list');
    questsList.innerHTML = quests.map(quest => `
        <div class="quest-card">
            <h3>${quest.name}</h3>
            <p>${quest.description}</p>
            <p>Награда: ${quest.reward} CP</p>
            <button class="btn btn-primary" onclick="completeQuest('${quest.id}')">Завершить</button>
        </div>
    `).join('');
}

// Завершение квеста
function completeQuest(questId) {
    const quest = quests.find(q => q.id === questId);
    if (quest) {
        quest.completed = true;
        updateBalance(quest.reward);
        localStorage.setItem('quests', JSON.stringify(quests));
        renderQuests();
    }
}

// Рендер пресетов
function renderPresets() {
    const presetsList = document.getElementById('presets-list');
    presetsList.innerHTML = presets.map(preset => `
        <div class="preset-card" onclick="window.location.href='preset.html?id=${preset.id}'">
            <h3>${preset.name}</h3>
            <p>${preset.description}</p>
            <p>❤️ ${preset.likes}</p>
        </div>
    `).join('');
}

// Инициализация при загрузке
document.addEventListener('DOMContentLoaded', () => {
    renderPresets();
    renderQuests();
});

// Синхронизация темы с Telegram
function loadTheme() {
    const theme = tg.colorScheme;
    document.documentElement.setAttribute('data-theme', theme);
    tg.setHeaderColor(theme === 'dark' ? '#2d3748' : '#f8fafc');
}

// Валидация формы загрузки
function validatePresetForm() {
    const file = document.getElementById('presetFile').files[0];
    if (file.size > 2 * 1024 * 1024) {
        tg.showAlert("Файл не должен превышать 2 МБ");
        tg.HapticFeedback.notificationOccurred('error');
        return false;
    }
    return true;
}

// Отправка пресета через Telegram
document.getElementById('upload-preset-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData();
    formData.append('file', document.getElementById('presetFile').files[0]);

    try {
        const response = await tg.sendData(JSON.stringify({
            method: 'uploadPreset',
            userId: userData.user.id,
            formData,
        }));
        if (response.ok) {
            tg.showAlert("Пресет загружен!");
            tg.HapticFeedback.notificationOccurred('success');
            updateBalance(10);
            checkAchievements('upload');
        }
    } catch (error) {
        tg.showAlert("Ошибка загрузки");
    }
});

// Кнопка "Поделиться"
const shareBtn = new tg.Button('Поделиться', () => {
    tg.share({
        title: 'Пресеты',
        text: 'Посмотрите этот пресет!',
        url: window.location.href,
    });
});
tg.MainButton.setParams({ is_visible: true }).setText("Поделиться");

// Система достижений
const achievements = [
    { id: 1, name: 'Новичок', description: 'Загрузите первый пресет', target: 1, progress: 0, completed: false },
    { id: 2, name: 'Энтузиаст', description: 'Загрузите 5 пресетов', target: 5, progress: 0, completed: false },
    { id: 3, name: 'Социальный', description: 'Оставьте 10 комментариев', target: 10, progress: 0, completed: false },
    { id: 4, name: 'Популярный', description: 'Получите 50 лайков', target: 50, progress: 0, completed: false },
    { id: 5, name: 'Исследователь', description: 'Прослушайте 20 пресетов', target: 20, progress: 0, completed: false },
];

function checkAchievements(type) {
    achievements.forEach(achievement => {
        switch (achievement.id) {
            case 1:
                if (type === 'upload') achievement.progress++;
                break;
            case 3:
                if (type === 'comment') achievement.progress++;
                break;
            case 4:
                if (type === 'like') achievement.progress++;
                break;
        }

        if (achievement.progress >= achievement.target && !achievement.completed) {
            achievement.completed = true;
            tg.showAlert(`🎉 Достижение "${achievement.name}" выполнено!`);
        }
    });
    updateAchievementsUI();
}

function updateAchievementsUI() {
    const achievementsSection = document.getElementById('achievements-section');
    if (!achievementsSection) return;

    achievementsSection.innerHTML = achievements.map(achievement => `
        <div class="achievement-card">
            <h3>${achievement.name}</h3>
            <p>${achievement.description}</p>
            <div class="progress-bar">
                <div style="width: ${(achievement.progress / achievement.target) * 100}%"></div>
            </div>
            <p>${achievement.completed ? '✅ Выполнено' : '❌ Не выполнено'}</p>
        </div>
    `).join('');
}

// Топ-пресеты
let presets = JSON.parse(localStorage.getItem('presets')) || [];
function updateTopPresets() {
    const sorted = [...presets].sort((a, b) => (b.likes || 0) - (a.likes || 0));
    const top10 = sorted.slice(0, 10);
    renderTopPresets(top10);
}

function renderTopPresets(data) {
    const container = document.getElementById('top-presets-list');
    container.innerHTML = data.map(preset => `
        <div class="preset-card" id="${preset.id}">
            <h3>${preset.name}</h3>
            <p>${preset.description}</p>
            <div class="preset-meta">
                <span>❤️ ${preset.likes || 0}</span>
                <button class="btn btn-icon" onclick="toggleLike('${preset.id}')">
                    <i class="fas fa-heart"></i>
                </button>
                <button class="btn btn-icon" onclick="showComments('${preset.id}')">
                    <i class="fas fa-comment"></i>
                </button>
            </div>
            <div class="comments-section" id="comments-${preset.id}"></div>
        </div>
    `).join('');
}

// Система комментариев и лайков
function addComment(presetId, text) {
    const preset = presets.find(p => p.id === presetId);
    if (!preset.comments) preset.comments = [];
    preset.comments.push({ user: userId, text, date: new Date() });
    localStorage.setItem('presets', JSON.stringify(presets));
    checkAchievements('comment');
    updateTopPresets();
}

function toggleLike(presetId) {
    const preset = presets.find(p => p.id === presetId);
    preset.likes = (preset.likes || 0) + 1;
    localStorage.setItem('presets', JSON.stringify(presets));
    checkAchievements('like');
    updateTopPresets();
}

function showComments(presetId) {
    const preset = presets.find(p => p.id === presetId);
    const commentsSection = document.getElementById(`comments-${presetId}`);
    commentsSection.innerHTML = preset.comments?.map(comment => `
        <div class="comment">
            <strong>${comment.user}:</strong> ${comment.text}
        </div>
    `).join('') || "Нет комментариев.";
}

function postComment() {
    const commentInput = document.getElementById('commentInput');
    const presetId = document.querySelector('.preset-card').id;
    if (commentInput.value.trim()) {
        addComment(presetId, commentInput.value.trim());
        commentInput.value = "";
        showComments(presetId);
    }
}

// Инициализация при загрузке
document.addEventListener('DOMContentLoaded', () => {
    loadTheme();
    tg.BackButton.show().onClick(() => window.history.back());
    updateTopPresets();
    updateAchievementsUI();

    // Пример: Добавление CP за активность
    setTimeout(() => {
        updateBalance(10);
        tg.showAlert('+10 CP за активность!');
    }, 60000); // Через 1 минуту
});
