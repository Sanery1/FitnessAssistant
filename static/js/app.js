/**
 * Fitness AI Assistant - Frontend
 */

// API 基础路径
const API_BASE = '/api';
const CHAT_REQUEST_TIMEOUT_MS = 45000;

// 当前用户 ID
let currentUserId = 'default';
let chatModelSelectRef = null;

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

    if (pageName === 'chat' && chatModelSelectRef) {
        loadLLMModels(chatModelSelectRef);
    }
}

// ==================== 聊天功能 ====================

function initChat() {
    const modelSelect = document.getElementById('chat-model-select');
    chatModelSelectRef = modelSelect;

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

    if (modelSelect) {
        initChatLLMSettings(modelSelect);
    }
}

async function sendMessage() {
    const message = elements.chatInput.value.trim();
    if (!message) return;

    // 添加用户消息
    addMessage('user', message);
    elements.chatInput.value = '';

    // 显示加载
    const loadingEl = addMessage('assistant', '思考中...', true);
    let timeoutId = null;

    try {
        const controller = new AbortController();
        timeoutId = setTimeout(() => controller.abort(), CHAT_REQUEST_TIMEOUT_MS);

        const response = await fetch(`${API_BASE}/chat/message`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            signal: controller.signal,
            body: JSON.stringify({
                message: message,
                user_id: currentUserId
            })
        });

        const data = await response.json();

        if (!response.ok) {
            const detail = String((data && data.detail) || '');
            const text = toFriendlyChatError(response.status, detail);
            throw new Error(text);
        }

        loadingEl.remove();
        addMessage('assistant', data.content);

    } catch (error) {
        loadingEl.remove();
        if (error && error.name === 'AbortError') {
            addMessage('assistant', '抱歉，响应超时，请稍后重试或切换其他模型。');
            return;
        }
        addMessage('assistant', '抱歉，发生了错误：' + error.message);
    } finally {
        if (timeoutId) {
            clearTimeout(timeoutId);
        }
    }
}

function toFriendlyChatError(status, detail) {
    const text = (detail || '').toLowerCase();

    if (text.includes('429') || text.includes('too many requests') || text.includes('rate limit')) {
        return '当前 AI 服务较忙，请稍后重试。';
    }

    if (text.includes('暂时不可用') || text.includes('temporarily unavailable')) {
        return '当前模型暂不可用，请切换模型后重试。';
    }

    if (status === 401 || text.includes('api key') || text.includes('unauthorized')) {
        return 'AI 服务鉴权失败，请联系管理员检查配置。';
    }

    if (text.includes('timeout') || text.includes('timed out')) {
        return 'AI 服务响应超时，请稍后重试。';
    }

    return '暂时无法获取 AI 回复，请稍后重试。';
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

    if (role === 'assistant') {
        contentEl.classList.add('message-markdown');
        contentEl.innerHTML = renderAssistantMarkdown(String(content ?? ''));
    } else {
        const paragraphEl = document.createElement('p');
        paragraphEl.textContent = String(content ?? '');
        contentEl.appendChild(paragraphEl);
    }

    msgEl.appendChild(avatarEl);
    msgEl.appendChild(contentEl);

    if (isLoading) {
        contentEl.classList.add('loading');
    }

    elements.chatMessages.appendChild(msgEl);
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;

    return msgEl;
}

function renderAssistantMarkdown(rawText) {
    const text = String(rawText || '').replace(/\r\n/g, '\n');
    const lines = text.split('\n');
    const htmlParts = [];
    let i = 0;

    while (i < lines.length) {
        const current = lines[i].trim();

        if (!current) {
            i += 1;
            continue;
        }

        if (/^---+$/.test(current)) {
            htmlParts.push('<hr>');
            i += 1;
            continue;
        }

        if (current.startsWith('```')) {
            const codeLines = [];
            i += 1;
            while (i < lines.length && !lines[i].trim().startsWith('```')) {
                codeLines.push(lines[i]);
                i += 1;
            }
            if (i < lines.length && lines[i].trim().startsWith('```')) {
                i += 1;
            }
            htmlParts.push(`<pre><code>${escapeHtml(codeLines.join('\n'))}</code></pre>`);
            continue;
        }

        const h3 = current.match(/^###\s+(.+)$/);
        const h2 = current.match(/^##\s+(.+)$/);
        const h1 = current.match(/^#\s+(.+)$/);
        if (h3) {
            htmlParts.push(`<h4>${inlineMarkdown(h3[1])}</h4>`);
            i += 1;
            continue;
        }
        if (h2) {
            htmlParts.push(`<h3>${inlineMarkdown(h2[1])}</h3>`);
            i += 1;
            continue;
        }
        if (h1) {
            htmlParts.push(`<h2>${inlineMarkdown(h1[1])}</h2>`);
            i += 1;
            continue;
        }

        if (isTableHeader(lines, i)) {
            const { html, nextIndex } = parseTable(lines, i);
            htmlParts.push(html);
            i = nextIndex;
            continue;
        }

        if (/^[-*]\s+/.test(current)) {
            const items = [];
            while (i < lines.length && /^[-*]\s+/.test(lines[i].trim())) {
                items.push(`<li>${inlineMarkdown(lines[i].trim().replace(/^[-*]\s+/, ''))}</li>`);
                i += 1;
            }
            htmlParts.push(`<ul>${items.join('')}</ul>`);
            continue;
        }

        if (/^\d+\.\s+/.test(current)) {
            const items = [];
            while (i < lines.length && /^\d+\.\s+/.test(lines[i].trim())) {
                items.push(`<li>${inlineMarkdown(lines[i].trim().replace(/^\d+\.\s+/, ''))}</li>`);
                i += 1;
            }
            htmlParts.push(`<ol>${items.join('')}</ol>`);
            continue;
        }

        if (/^>\s?/.test(current)) {
            const quoteLines = [];
            while (i < lines.length && /^>\s?/.test(lines[i].trim())) {
                quoteLines.push(lines[i].trim().replace(/^>\s?/, ''));
                i += 1;
            }
            htmlParts.push(`<blockquote>${inlineMarkdown(quoteLines.join('\n'))}</blockquote>`);
            continue;
        }

        htmlParts.push(`<p>${inlineMarkdown(current)}</p>`);
        i += 1;
    }

    return htmlParts.join('') || `<p>${escapeHtml(text)}</p>`;
}

function inlineMarkdown(text) {
    const escaped = escapeHtml(text);
    return escaped
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        .replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
}

function isTableHeader(lines, index) {
    if (index + 1 >= lines.length) return false;
    const line = lines[index].trim();
    const divider = lines[index + 1].trim();
    return line.includes('|') && /^\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?$/.test(divider);
}

function parseTable(lines, startIndex) {
    const headerCells = splitTableLine(lines[startIndex]);
    let rowIndex = startIndex + 2;
    const rows = [];

    while (rowIndex < lines.length) {
        const line = lines[rowIndex].trim();
        if (!line || !line.includes('|')) break;
        rows.push(splitTableLine(lines[rowIndex]));
        rowIndex += 1;
    }

    const thead = `<thead><tr>${headerCells.map(cell => `<th>${inlineMarkdown(cell)}</th>`).join('')}</tr></thead>`;
    const tbody = `<tbody>${rows.map(row => `<tr>${row.map(cell => `<td>${inlineMarkdown(cell)}</td>`).join('')}</tr>`).join('')}</tbody>`;
    return { html: `<table>${thead}${tbody}</table>`, nextIndex: rowIndex };
}

function splitTableLine(line) {
    return line
        .trim()
        .replace(/^\|/, '')
        .replace(/\|$/, '')
        .split('|')
        .map(item => item.trim());
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
        alert('设置已保存！');
    });
}

function initChatLLMSettings(modelSelect) {
    loadLLMModels(modelSelect);

    modelSelect.addEventListener('change', async () => {
        const selectedModel = String(modelSelect.value || '').trim();
        if (!selectedModel) return;

        try {
            const response = await fetch(`${API_BASE}/chat/active-llm`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ model: selectedModel })
            });

            const data = await response.json();
            if (!response.ok) {
                throw new Error(String(data.detail || '切换失败'));
            }

            if (data.active_model) {
                modelSelect.value = data.active_model;
            }
        } catch (error) {
            alert(`模型切换失败：${error.message}`);
            await loadLLMModels(modelSelect);
        }
    });
}

async function loadLLMModels(modelSelect) {
    try {
        const response = await fetch(`${API_BASE}/chat/llm-models`);
        const data = await response.json();
        if (!response.ok || !Array.isArray(data.models) || data.models.length === 0) return;

        modelSelect.innerHTML = '';
        data.models.forEach(model => {
            const option = document.createElement('option');
            option.value = model;
            option.textContent = model;
            modelSelect.appendChild(option);
        });

        if (data.active_model) {
            modelSelect.value = data.active_model;
        }
    } catch (_error) {
        // 静默失败，不阻塞页面主功能
    }
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
