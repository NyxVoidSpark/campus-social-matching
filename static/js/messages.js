// 消息中心页面JavaScript

let currentUser = null;
let currentChatUserId = null;
let conversations = [];
let messagePollingInterval = null;

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', function() {
    checkLoginStatus();
    
    // 检查URL参数，如果有user_id则直接打开聊天
    const urlParams = new URLSearchParams(window.location.search);
    const userId = urlParams.get('user_id');
    if (userId) {
        setTimeout(() => openChat(userId), 500);
    }
});

// 检查登录状态
function checkLoginStatus() {
    fetch('/api/current-user')
        .then(response => {
            if (response.status === 401) {
                window.location.href = '/login';
                return;
            }
            return response.json();
        })
        .then(result => {
            if (result.success) {
                currentUser = result.data;
                loadConversations();
                // 开始轮询未读消息
                startMessagePolling();
            }
        })
        .catch(error => {
            console.error('检查登录状态失败:', error);
            window.location.href = '/login';
        });
}

// 加载会话列表
function loadConversations() {
    fetch('/api/messages/conversations')
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                conversations = result.data;
                displayConversations(result.data);
            } else {
                console.error('加载会话列表失败:', result.error);
            }
        })
        .catch(error => {
            console.error('加载会话列表失败:', error);
        });
}

// 显示会话列表
function displayConversations(conversationsList) {
    const container = document.getElementById('conversationsList');
    
    if (conversationsList.length === 0) {
        container.innerHTML = `
            <div class="text-center p-4">
                <i class="fas fa-comments"></i>
                <p class="mt-2 text-muted">还没有会话，快去和好友聊天吧！</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = conversationsList.map(conv => `
        <div class="conversation-item ${conv.user_id === currentChatUserId ? 'active' : ''}" 
             onclick="openChat('${conv.user_id}')">
            <div class="d-flex align-items-center">
                <img src="${conv.avatar || '/static/images/default.jpg'}" 
                     alt="${conv.username}" 
                     class="conversation-avatar"
                     onerror="this.src='/static/images/default.jpg'">
                <div class="conversation-info">
                    <div class="d-flex justify-content-between align-items-center">
                        <span class="conversation-name">${conv.username}</span>
                        <span class="conversation-time">${formatTime(conv.last_message_time)}</span>
                    </div>
                    <div class="d-flex justify-content-between align-items-center">
                        <span class="conversation-preview">${conv.is_own_last_message ? '我: ' : ''}${conv.last_message}</span>
                        ${conv.unread_count > 0 ? `<span class="unread-badge">${conv.unread_count}</span>` : ''}
                    </div>
                </div>
            </div>
        </div>
    `).join('');
}

// 打开聊天
function openChat(userId) {
    currentChatUserId = userId;
    
    // 更新会话列表的active状态
    document.querySelectorAll('.conversation-item').forEach(item => {
        item.classList.remove('active');
    });
    event?.currentTarget?.classList.add('active');
    
    // 加载聊天记录
    loadMessages(userId);
    
    // 显示聊天区域
    const chatArea = document.getElementById('chatArea');
    chatArea.classList.add('active');
    
    // 在移动端可能需要特殊处理
    if (window.innerWidth <= 768) {
        document.querySelector('.conversations-list').style.display = 'none';
    }
}

// 加载消息
function loadMessages(userId) {
    fetch(`/api/messages/${userId}`)
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                displayMessages(result.data, result.target_user);
                // 滚动到底部
                setTimeout(() => scrollToBottom(), 100);
            } else {
                showError('加载消息失败: ' + result.error);
            }
        })
        .catch(error => {
            console.error('加载消息失败:', error);
            showError('加载消息失败');
        });
}

// 显示消息
function displayMessages(messages, targetUser) {
    const chatArea = document.getElementById('chatArea');
    
    if (!targetUser) {
        chatArea.innerHTML = `
            <div class="empty-chat">
                <i class="fas fa-comments"></i>
                <p>用户不存在</p>
            </div>
        `;
        return;
    }
    
    chatArea.innerHTML = `
        <div class="chat-header">
            <div class="d-flex align-items-center">
                <img src="${targetUser.avatar || '/static/images/default.jpg'}" 
                     alt="${targetUser.username}" 
                     class="conversation-avatar me-3"
                     onerror="this.src='/static/images/default.jpg'">
                <div>
                    <h5 class="mb-0">${targetUser.username}</h5>
                </div>
            </div>
        </div>
        <div class="chat-messages" id="chatMessages">
            ${messages.length === 0 ? `
                <div class="empty-chat">
                    <i class="fas fa-comments"></i>
                    <p>还没有消息，开始聊天吧！</p>
                </div>
            ` : messages.map(msg => `
                <div class="message-item ${msg.is_own ? 'own' : 'other'}">
                    <div class="message-bubble">
                        <div>${escapeHtml(msg.content)}</div>
                        <div class="message-time">${formatTime(msg.created_at)}</div>
                    </div>
                </div>
            `).join('')}
        </div>
        <div class="chat-input-area">
            <div class="input-group">
                <input type="text" class="form-control" id="messageInput" placeholder="输入消息..." 
                       onkeypress="handleMessageKeyPress(event)">
                <button class="btn btn-primary" onclick="sendMessage()">
                    <i class="fas fa-paper-plane"></i> 发送
                </button>
            </div>
        </div>
    `;
}

// 发送消息
function sendMessage() {
    const input = document.getElementById('messageInput');
    const content = input.value.trim();
    
    if (!content) {
        return;
    }
    
    if (!currentChatUserId) {
        showError('请先选择一个会话');
        return;
    }
    
    fetch('/api/messages', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            receiver_id: currentChatUserId,
            content: content
        })
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            input.value = '';
            // 重新加载消息
            loadMessages(currentChatUserId);
            // 重新加载会话列表
            loadConversations();
        } else {
            showError('发送失败: ' + result.error);
        }
    })
    .catch(error => {
        console.error('发送消息失败:', error);
        showError('发送失败');
    });
}

// 处理回车键发送
function handleMessageKeyPress(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

// 滚动到底部
function scrollToBottom() {
    const chatMessages = document.getElementById('chatMessages');
    if (chatMessages) {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

// 格式化时间
function formatTime(timeString) {
    if (!timeString) return '';
    
    const now = new Date();
    const time = new Date(timeString);
    const diff = now - time;
    
    // 如果是今天
    if (diff < 24 * 60 * 60 * 1000 && time.getDate() === now.getDate()) {
        return time.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
    }
    
    // 如果是今年
    if (time.getFullYear() === now.getFullYear()) {
        return time.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' });
    }
    
    // 其他情况显示完整日期
    return time.toLocaleDateString('zh-CN');
}

// HTML转义
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 开始消息轮询
function startMessagePolling() {
    // 每30秒轮询一次未读消息
    messagePollingInterval = setInterval(() => {
        loadConversations();
        if (currentChatUserId) {
            loadMessages(currentChatUserId);
        }
    }, 30000);
}

// 停止消息轮询
function stopMessagePolling() {
    if (messagePollingInterval) {
        clearInterval(messagePollingInterval);
        messagePollingInterval = null;
    }
}

// 页面卸载时停止轮询
window.addEventListener('beforeunload', stopMessagePolling);

// 显示错误消息
function showError(message) {
    const alert = document.createElement('div');
    alert.className = 'alert alert-danger alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3';
    alert.style.zIndex = '9999';
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alert);
    setTimeout(() => alert.remove(), 3000);
}
