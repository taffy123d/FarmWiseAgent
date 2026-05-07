const appContainer = document.getElementById('app-container');
const chatContainer = document.getElementById('chat-container');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');
const loadBtn = document.getElementById('load-btn');
const loadStatus = document.getElementById('load-status');
const sidebarToggle = document.getElementById('sidebar-toggle');

let isLoading = false;

// 侧边栏折叠
sidebarToggle.addEventListener('click', () => {
    appContainer.classList.toggle('collapsed');
    sidebarToggle.title = appContainer.classList.contains('collapsed') ? '展开侧边栏' : '收起侧边栏';
});

function createMessageElement(role, content) {
    const wrapper = document.createElement('div');
    wrapper.className = `message ${role}`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = role === 'user' ? '我' : 'AI';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = content;

    if (role === 'user') {
        wrapper.appendChild(contentDiv);
        wrapper.appendChild(avatar);
    } else {
        wrapper.appendChild(avatar);
        wrapper.appendChild(contentDiv);
    }

    chatContainer.appendChild(wrapper);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    return contentDiv;
}

function createAssistantMessageElement() {
    const wrapper = document.createElement('div');
    wrapper.className = 'message assistant';

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = 'AI';

    const body = document.createElement('div');
    body.className = 'message-body';

    // Thinking section (collapsible)
    const thinkingSection = document.createElement('div');
    thinkingSection.className = 'thinking-section collapsed';

    const toggleBtn = document.createElement('button');
    toggleBtn.className = 'toggle-thinking';
    toggleBtn.textContent = '查看推理过程';

    const thinkingContent = document.createElement('div');
    thinkingContent.className = 'thinking-content';

    toggleBtn.addEventListener('click', () => {
        thinkingSection.classList.toggle('collapsed');
        toggleBtn.textContent = thinkingSection.classList.contains('collapsed')
            ? '查看推理过程'
            : '隐藏推理过程';
    });

    thinkingSection.appendChild(toggleBtn);
    thinkingSection.appendChild(thinkingContent);

    // Final answer section (markdown)
    const finalSection = document.createElement('div');
    finalSection.className = 'final-section markdown-body';

    body.appendChild(thinkingSection);
    body.appendChild(finalSection);
    wrapper.appendChild(avatar);
    wrapper.appendChild(body);
    chatContainer.appendChild(wrapper);
    chatContainer.scrollTop = chatContainer.scrollHeight;

    return {
        wrapper,
        thinkingSection,
        thinkingContent,
        finalSection
    };
}

function showThinking() {
    const wrapper = document.createElement('div');
    wrapper.className = 'message assistant';
    wrapper.id = 'thinking-msg';

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = 'AI';

    const thinking = document.createElement('div');
    thinking.className = 'thinking';
    thinking.innerHTML = '智能客服思考中<div class="typing-indicator"><span></span><span></span><span></span></div>';

    wrapper.appendChild(avatar);
    wrapper.appendChild(thinking);
    chatContainer.appendChild(wrapper);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function removeThinking() {
    const el = document.getElementById('thinking-msg');
    if (el) el.remove();
}

async function sendMessage() {
    const query = chatInput.value.trim();
    if (!query || isLoading) return;

    chatInput.value = '';
    createMessageElement('user', query);
    showThinking();

    isLoading = true;
    updateUI();

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        removeThinking();
        const assistant = createAssistantMessageElement();
        let finalText = '';

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const parts = buffer.split('\n\n');
            buffer = parts.pop();

            for (const part of parts) {
                const lines = part.split('\n');
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const dataStr = line.slice(6).trim();
                        if (!dataStr) continue;
                        try {
                            const data = JSON.parse(dataStr);
                            if (data.type === 'thinking') {
                                assistant.thinkingContent.textContent += data.chunk;
                                assistant.thinkingSection.classList.add('has-content');
                                chatContainer.scrollTop = chatContainer.scrollHeight;
                            } else if (data.type === 'final') {
                                finalText += data.chunk;
                                assistant.finalSection.innerHTML = marked.parse(finalText);
                                assistant.finalSection.classList.add('streaming-cursor');
                                chatContainer.scrollTop = chatContainer.scrollHeight;
                            } else if (data.type === 'error') {
                                assistant.finalSection.innerHTML = '<p style="color:#e74c3c">出错了: ' + escapeHtml(data.chunk) + '</p>';
                            } else if (data.type === 'done') {
                                isLoading = false;
                                assistant.finalSection.classList.remove('streaming-cursor');
                                updateUI();
                            }
                        } catch (e) {
                            console.error('Parse SSE data error:', e, dataStr);
                        }
                    }
                }
            }
        }

        // Process remaining buffer
        if (buffer.trim()) {
            const lines = buffer.split('\n');
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const dataStr = line.slice(6).trim();
                    if (!dataStr) continue;
                    try {
                        const data = JSON.parse(dataStr);
                        if (data.type === 'done') {
                            isLoading = false;
                            updateUI();
                        }
                    } catch (e) {}
                }
            }
        }

        // Ensure markdown is fully rendered at the end
        if (finalText) {
            assistant.finalSection.innerHTML = marked.parse(finalText);
        }
    } catch (err) {
        removeThinking();
        const assistant = createAssistantMessageElement();
        assistant.finalSection.innerHTML = '<p style="color:#e74c3c">请求失败，请稍后重试。</p>';
        isLoading = false;
        updateUI();
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function updateUI() {
    sendBtn.disabled = isLoading;
    chatInput.disabled = isLoading;
    if (!isLoading) chatInput.focus();
}

sendBtn.addEventListener('click', sendMessage);
chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') sendMessage();
});

loadBtn.addEventListener('click', async () => {
    if (loadBtn.disabled) return;
    loadBtn.disabled = true;
    loadStatus.textContent = '正在加载文档到向量库...';
    loadStatus.className = 'status-text';

    try {
        const res = await fetch('/api/load-knowledge', { method: 'POST' });
        const data = await res.json();
        loadStatus.textContent = data.message;
        loadStatus.className = `status-text ${data.status}`;
    } catch (e) {
        loadStatus.textContent = '加载失败: ' + e.message;
        loadStatus.className = 'status-text error';
    } finally {
        loadBtn.disabled = false;
    }
});

// 变更用户ID
const userIdInput = document.getElementById('user-id-input');
const setUserIdBtn = document.getElementById('set-user-id-btn');
const userIdStatus = document.getElementById('user-id-status');

// 页面加载时获取当前 user_id
(async () => {
    try {
        const res = await fetch('/api/get-user-id', { method: 'POST' });
        const data = await res.json();
        if (data.user_id) userIdInput.value = data.user_id;
    } catch (e) {}
})();

setUserIdBtn.addEventListener('click', async () => {
    const uid = userIdInput.value.trim();
    if (!/^\d{4}$/.test(uid)) {
        userIdStatus.textContent = '请输入4位数字';
        userIdStatus.style.color = '#e74c3c';
        return;
    }
    setUserIdBtn.disabled = true;
    try {
        const res = await fetch('/api/set-user-id', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: uid })
        });
        const data = await res.json();
        userIdStatus.textContent = data.message;
        userIdStatus.style.color = data.status === 'success' ? '#2ecc71' : '#e74c3c';
    } catch (e) {
        userIdStatus.textContent = '请求失败: ' + e.message;
        userIdStatus.style.color = '#e74c3c';
    } finally {
        setUserIdBtn.disabled = false;
    }
});

userIdInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') setUserIdBtn.click();
});

const clearMemoryBtn = document.getElementById('clear-memory-btn');
clearMemoryBtn.addEventListener('click', async () => {
    if (clearMemoryBtn.disabled) return;
    clearMemoryBtn.disabled = true;
    clearMemoryBtn.textContent = '清空中...';
    try {
        const res = await fetch('/api/clear-session', { method: 'POST' });
        const data = await res.json();
        loadStatus.textContent = data.message;
        loadStatus.className = `status-text ${data.status}`;
        chatContainer.innerHTML = '';
    } catch (e) {
        loadStatus.textContent = '清空失败: ' + e.message;
        loadStatus.className = 'status-text error';
    } finally {
        clearMemoryBtn.disabled = false;
        clearMemoryBtn.textContent = '清空对话记忆';
    }
});

chatInput.focus();
