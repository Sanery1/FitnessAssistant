/**
 * Fitness AI Assistant - Frontend
 */

// API 基础路径
const API_BASE = '/api';

// 当前用户 ID
let currentUserId = 'default';

// DOM 元素
const elements = {
    chatMessages: document.getElementById('chat-messages'),
    chatInput: document.getElementById('chat-input'),
    sendBtn: document.getElementById('send-btn'),
    quickBtns: document.querySelectorAll('.quick-btn'),
    navItems: document.querySelectorAll('.nav-item'),
    pages: document.querySelectorAll('.page')
};

function escapeHtml(value) {
    return String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

// ==================== 页面导航 ====================

function initNavigation() {
    elements.navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const page = item.dataset.page;
            switchPage(page);
        });
    });
}

function switchPage(pageName) {
    // 更新导航
    elements.navItems.forEach(item => {
        item.classList.toggle('active', item.dataset.page === pageName);
    });

    // 切换页面
    elements.pages.forEach(page => {
        page.classList.toggle('active', page.id === `page-${pageName}`);
    });
}

// ==================== 聊天功能 ====================

function initChat() {
    // 发送按钮
    elements.sendBtn.addEventListener('click', sendMessage);

    // 回车发送
    elements.chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // 快捷按钮
    elements.quickBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const msg = btn.dataset.msg;
            elements.chatInput.value = msg;
            sendMessage();
        });
    });

    // 自动调整输入框高度
    elements.chatInput.addEventListener('input', () => {
        elements.chatInput.style.height = 'auto';
        elements.chatInput.style.height = elements.chatInput.scrollHeight + 'px';
    });
}

async function sendMessage() {
    const message = elements.chatInput.value.trim();
    if (!message) return;

    // 添加用户消息
    addMessage('user', message);
    elements.chatInput.value = '';

    // 显示加载
    const loadingEl = addMessage('assistant', '思考中...', true);

    try {
        const response = await fetch(`${API_BASE}/chat/message`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                user_id: currentUserId
            })
        });

        const data = await response.json();
        loadingEl.remove();
        addMessage('assistant', data.content);

    } catch (error) {
        loadingEl.remove();
        addMessage('assistant', '抱歉，发生了错误：' + error.message);
    }
}

function addMessage(role, content, isLoading = false) {
    const msgEl = document.createElement('div');
    msgEl.className = `message ${role}`;

    const avatar = role === 'user' ? '👤' : '💪';

    const avatarEl = document.createElement('div');
    avatarEl.className = 'message-avatar';
    avatarEl.textContent = avatar;

    const contentEl = document.createElement('div');
    contentEl.className = 'message-content';

    const paragraphEl = document.createElement('p');
    paragraphEl.textContent = String(content ?? '');
    contentEl.appendChild(paragraphEl);

    msgEl.appendChild(avatarEl);
    msgEl.appendChild(contentEl);

    if (isLoading) {
        contentEl.classList.add('loading');
    }

    elements.chatMessages.appendChild(msgEl);
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;

    return msgEl;
}

// ==================== 训练计划 ====================

function initWorkout() {
    const form = document.getElementById('workout-form');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(form);

        const resultDiv = document.getElementById('workout-result');
        const contentDiv = document.getElementById('workout-plan-content');

        resultDiv.classList.remove('hidden');
        contentDiv.innerHTML = '<div class="loading"></div>';

        try {
            const response = await fetch(`${API_BASE}/workout/generate-plan`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    goal: formData.get('goal'),
                    level: formData.get('level'),
                    days_per_week: parseInt(formData.get('days')),
                    minutes_per_day: parseInt(formData.get('duration'))
                })
            });

            const data = await response.json();
            renderWorkoutPlan(data);

        } catch (error) {
            contentDiv.innerHTML = `<p>生成失败：${escapeHtml(error.message)}</p>`;
        }
    });
}

function renderWorkoutPlan(plan) {
    const contentDiv = document.getElementById('workout-plan-content');

    let html = `<p><strong>计划名称：</strong>${escapeHtml(plan.name)}</p>`;
    html += `<p><strong>持续周数：</strong>${escapeHtml(plan.duration_weeks)} 周</p>`;
    html += `<p><strong>每周训练：</strong>${escapeHtml(plan.sessions_per_week)} 次</p>`;

    plan.sessions.forEach(session => {
        html += `
            <div class="session-card">
                <h4>第 ${escapeHtml(session.day)} 天 - ${escapeHtml(session.name)}</h4>
                <p>时长：${escapeHtml(session.duration_minutes)} 分钟</p>
                <p>目标肌群：${escapeHtml((session.muscles || []).join(', '))}</p>
                <h5>动作列表：</h5>
        `;

        session.exercises.forEach(ex => {
            html += `
                <div class="exercise-item">
                    <span>${escapeHtml(ex.name)}</span>
                    <span>${escapeHtml(ex.sets)} 组 × ${escapeHtml(ex.reps)}</span>
                </div>
            `;
        });

        html += `</div>`;
    });

    contentDiv.innerHTML = html;
}

// ==================== 营养分析 ====================

function initNutrition() {
    const form = document.getElementById('nutrition-form');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(form);

        const resultDiv = document.getElementById('nutrition-result');
        const contentDiv = document.getElementById('nutrition-content');

        resultDiv.classList.remove('hidden');
        contentDiv.innerHTML = '<div class="loading"></div>';

        try {
            const response = await fetch(`${API_BASE}/nutrition/calculate-calories`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    gender: formData.get('gender'),
                    age: parseInt(formData.get('age')),
                    height: parseFloat(formData.get('height')),
                    weight: parseFloat(formData.get('weight')),
                    activity_level: formData.get('activity'),
                    goal: formData.get('goal')
                })
            });

            const data = await response.json();
            renderNutritionResult(data);

        } catch (error) {
            contentDiv.innerHTML = `<p>计算失败：${escapeHtml(error.message)}</p>`;
        }
    });
}

function renderNutritionResult(data) {
    const contentDiv = document.getElementById('nutrition-content');

    let html = `
        <div class="macros-display">
            <div class="macro-item">
                <div class="macro-value">${escapeHtml(data.target_calories)}</div>
                <div class="macro-label">每日热量 (kcal)</div>
            </div>
            <div class="macro-item">
                <div class="macro-value">${escapeHtml(data.tdee)}</div>
                <div class="macro-label">每日消耗 (TDEE)</div>
            </div>
            <div class="macro-item">
                <div class="macro-value">${escapeHtml(data.bmr)}</div>
                <div class="macro-label">基础代谢 (BMR)</div>
            </div>
        </div>

        <div class="macros-display">
            <div class="macro-item">
                <div class="macro-value">${escapeHtml(data.macros.protein.grams)}g</div>
                <div class="macro-label">蛋白质</div>
                <div class="macro-grams">${escapeHtml(data.macros.protein.calories)} kcal</div>
            </div>
            <div class="macro-item">
                <div class="macro-value">${escapeHtml(data.macros.carbs.grams)}g</div>
                <div class="macro-label">碳水化合物</div>
                <div class="macro-grams">${escapeHtml(data.macros.carbs.calories)} kcal</div>
            </div>
            <div class="macro-item">
                <div class="macro-value">${escapeHtml(data.macros.fat.grams)}g</div>
                <div class="macro-label">脂肪</div>
                <div class="macro-grams">${escapeHtml(data.macros.fat.calories)} kcal</div>
            </div>
        </div>

        <h4>营养建议</h4>
        <ul>
    `;

    (data.tips || []).forEach(tip => {
        html += `<li>${escapeHtml(tip)}</li>`;
    });

    html += '</ul>';
    contentDiv.innerHTML = html;
}

// ==================== 身体数据 ====================

function initBodyData() {
    const form = document.getElementById('body-form');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(form);

        const resultDiv = document.getElementById('body-result');
        const contentDiv = document.getElementById('body-content');

        resultDiv.classList.remove('hidden');
        contentDiv.innerHTML = '<div class="loading"></div>';

        try {
            const response = await fetch(`${API_BASE}/body/calculate-bmi`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    height: parseFloat(formData.get('height')),
                    weight: parseFloat(formData.get('weight'))
                })
            });

            const data = await response.json();
            renderBodyResult(data);

        } catch (error) {
            contentDiv.innerHTML = `<p>计算失败：${escapeHtml(error.message)}</p>`;
        }
    });
}

function renderBodyResult(data) {
    const contentDiv = document.getElementById('body-content');

    // 更新统计卡片
    document.getElementById('bmi-value').textContent = String(data.bmi ?? '--');
    document.getElementById('weight-value').textContent = `${data.ideal_weight_range.min}-${data.ideal_weight_range.max} kg`;

    let html = `
        <div class="macros-display">
            <div class="macro-item">
                <div class="macro-value">${escapeHtml(data.bmi)}</div>
                <div class="macro-label">BMI</div>
            </div>
            <div class="macro-item">
                <div class="macro-value">${escapeHtml(data.category)}</div>
                <div class="macro-label">体型分类</div>
            </div>
            <div class="macro-item">
                <div class="macro-value">${escapeHtml(data.ideal_weight_range.min)}-${escapeHtml(data.ideal_weight_range.max)}</div>
                <div class="macro-label">理想体重 (kg)</div>
            </div>
        </div>

        <p><strong>健康建议：</strong>${escapeHtml(data.advice)}</p>
        <p><strong>健康风险：</strong>${escapeHtml(data.health_risk)}</p>
    `;

    contentDiv.innerHTML = html;
}

// ==================== 设置 ====================

function initSettings() {
    const form = document.getElementById('settings-form');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(form);

        alert('设置已保存！');
    });
}

// ==================== 初始化 ====================

document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initChat();
    initWorkout();
    initNutrition();
    initBodyData();
    initSettings();

    console.log('🚀 Fitness AI Assistant 已加载');
});
