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

let llmFailoverLogsCache = [];

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

        if (!response.ok) {
            const detail = String((data && data.detail) || '');
            const text = toFriendlyChatError(response.status, detail);
            throw new Error(text);
        }

        loadingEl.remove();
        addMessage('assistant', data.content);

    } catch (error) {
        loadingEl.remove();
        addMessage('assistant', '抱歉，发生了错误：' + error.message);
    }
}

function toFriendlyChatError(status, detail) {
    const text = (detail || '').toLowerCase();

    if (status === 503 || text.includes('429') || text.includes('too many requests')) {
        return '当前 AI 服务较忙，请稍后重试。';
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

    loadLLMConfig(form);
    loadLLMFailoverLogs();

    const refreshBtn = document.getElementById('refresh-llm-logs-btn');
    const modelFilter = document.getElementById('llm-log-model-filter');
    const keywordInput = document.getElementById('llm-log-keyword');

    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            loadLLMFailoverLogs();
        });
    }
    if (modelFilter) {
        modelFilter.addEventListener('change', () => renderLLMFailoverLogs());
    }
    if (keywordInput) {
        keywordInput.addEventListener('input', () => renderLLMFailoverLogs());
    }

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(form);

        const payload = {
            provider: String(formData.get('llm_provider') || 'glm').trim(),
            base_url: String(formData.get('llm_base_url') || '').trim(),
            model: String(formData.get('llm_model') || '').trim(),
            api_key: String(formData.get('llm_api_key') || '').trim()
        };

        const fallbackText = String(formData.get('llm_fallback_models') || '').trim();
        const fallbackModels = fallbackText
            .split(',')
            .map(item => item.trim())
            .filter(Boolean);

        const poolConfigs = [
            {
                provider: payload.provider,
                base_url: payload.base_url,
                model: payload.model,
                api_key: payload.api_key
            },
            ...fallbackModels.map(model => ({
                provider: payload.provider,
                base_url: payload.base_url,
                model,
                api_key: payload.api_key
            }))
        ];

        try {
            const response = await fetch(`${API_BASE}/chat/llm-pool`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    active_index: 0,
                    auto_fallback_enabled: true,
                    fallback_cooldown_seconds: 120,
                    configs: poolConfigs
                })
            });

            const data = await response.json();
            if (!response.ok) {
                throw new Error(String(data.detail || '保存失败'));
            }

            const providerEl = form.querySelector('[name="llm_provider"]');
            const baseEl = form.querySelector('[name="llm_base_url"]');
            const modelEl = form.querySelector('[name="llm_model"]');
            const fallbackEl = form.querySelector('[name="llm_fallback_models"]');
            const keyEl = form.querySelector('[name="llm_api_key"]');

            if (providerEl && data.configs && data.configs.length > 0) providerEl.value = data.configs[0].provider || providerEl.value;
            if (baseEl && data.configs && data.configs.length > 0) baseEl.value = data.configs[0].base_url || '';
            if (modelEl && data.configs && data.configs.length > 0) modelEl.value = data.configs[0].model || '';
            if (fallbackEl && data.configs && data.configs.length > 1) {
                fallbackEl.value = data.configs.slice(1).map(item => item.model).join(',');
            }
            if (keyEl) keyEl.value = '';
            loadLLMFailoverLogs();

            alert('LLM 池配置已保存，新的对话请求将立即生效。');
        } catch (error) {
            alert(`保存失败：${error.message}`);
        }
    });
}

async function loadLLMFailoverLogs() {
    const panel = document.getElementById('llm-log-panel');
    if (!panel) return;

    try {
        const response = await fetch(`${API_BASE}/chat/llm-failover-logs?limit=20`);
        const data = await response.json();
        if (!response.ok || !Array.isArray(data.logs)) {
            llmFailoverLogsCache = [];
            panel.textContent = '暂无日志';
            return;
        }

        llmFailoverLogsCache = data.logs;
        if (llmFailoverLogsCache.length === 0) {
            panel.textContent = '暂无日志';
            return;
        }

        refreshLLMLogFilterOptions(llmFailoverLogsCache);
        renderLLMFailoverLogs();
    } catch (_err) {
        llmFailoverLogsCache = [];
        panel.textContent = '日志加载失败';
    }
}

function refreshLLMLogFilterOptions(logs) {
    const modelFilter = document.getElementById('llm-log-model-filter');
    if (!modelFilter) return;

    const current = modelFilter.value;
    const models = new Set();
    logs.forEach(item => {
        if (item.from_model) models.add(item.from_model);
        if (item.to_model) models.add(item.to_model);
    });

    modelFilter.innerHTML = '<option value="">全部模型</option>';
    Array.from(models).forEach(model => {
        const opt = document.createElement('option');
        opt.value = model;
        opt.textContent = model;
        modelFilter.appendChild(opt);
    });

    if (current && Array.from(models).includes(current)) {
        modelFilter.value = current;
    }
}

function renderLLMFailoverLogs() {
    const panel = document.getElementById('llm-log-panel');
    const modelFilter = document.getElementById('llm-log-model-filter');
    const keywordInput = document.getElementById('llm-log-keyword');
    if (!panel) return;

    const selectedModel = (modelFilter && modelFilter.value) ? modelFilter.value : '';
    const keyword = (keywordInput && keywordInput.value) ? keywordInput.value.trim().toLowerCase() : '';

    const filtered = llmFailoverLogsCache.filter(item => {
        if (selectedModel && item.from_model !== selectedModel && item.to_model !== selectedModel) {
            return false;
        }

        if (!keyword) {
            return true;
        }

        const haystack = [
            item.event,
            item.reason,
            item.from_model,
            item.to_model,
            String(item.from_index),
            String(item.to_index)
        ].join(' ').toLowerCase();

        return haystack.includes(keyword);
    });

    if (filtered.length === 0) {
        panel.textContent = '暂无匹配日志';
        return;
    }

    const lines = filtered.map(item => {
        const ts = item.ts ? new Date(item.ts * 1000).toLocaleString() : '-';
        const fromModel = item.from_model || '-';
        const toModel = item.to_model || '-';
        return `${ts} | ${item.event} | ${item.from_index}(${fromModel}) -> ${item.to_index}(${toModel}) | ${item.reason}`;
    });
    panel.textContent = lines.join('\n');
}

async function loadLLMConfig(form) {
    try {
        const response = await fetch(`${API_BASE}/chat/llm-pool`);
        const data = await response.json();
        if (!response.ok || !data.configs || data.configs.length === 0) return;

        const providerEl = form.querySelector('[name="llm_provider"]');
        const baseEl = form.querySelector('[name="llm_base_url"]');
        const modelEl = form.querySelector('[name="llm_model"]');
        const fallbackEl = form.querySelector('[name="llm_fallback_models"]');

        const first = data.configs[0];
        if (providerEl && first.provider) providerEl.value = first.provider;
        if (baseEl && first.base_url) baseEl.value = first.base_url;
        if (modelEl && first.model) modelEl.value = first.model;
        if (fallbackEl) {
            fallbackEl.value = data.configs.slice(1).map(item => item.model).join(',');
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
