// 好友管理页面JavaScript

let currentUser = null;

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', function() {
    checkLoginStatus();
    setupTabListeners();
    // 检查URL参数，如果有tab参数则切换到对应标签页（延迟执行确保Bootstrap已加载）
    setTimeout(() => {
        handleUrlTabParam();
    }, 100);
    
    // 支持回车键搜索
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                searchUsers();
            }
        });
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
                loadFriends();
                loadFriendRequests();
            }
        })
        .catch(error => {
            console.error('检查登录状态失败:', error);
            window.location.href = '/login';
        });
}

// 处理URL中的tab参数
function handleUrlTabParam() {
    const urlParams = new URLSearchParams(window.location.search);
    const tab = urlParams.get('tab');
    
    if (tab === 'search') {
        // 切换到"添加好友"标签页
        const searchTab = document.getElementById('search-tab');
        if (searchTab) {
            const bsTab = new bootstrap.Tab(searchTab);
            bsTab.show();
        }
    } else if (tab === 'requests') {
        // 切换到"好友请求"标签页
        const requestsTab = document.getElementById('requests-tab');
        if (requestsTab) {
            const bsTab = new bootstrap.Tab(requestsTab);
            bsTab.show();
        }
    }
    // 如果没有tab参数或tab=friends，默认显示"我的好友"标签页
}

// 设置标签页监听器
function setupTabListeners() {
    const tabs = document.querySelectorAll('#friendsTabs button[data-bs-toggle="tab"]');
    tabs.forEach(tab => {
        tab.addEventListener('shown.bs.tab', function(event) {
            const targetId = event.target.getAttribute('data-bs-target');
            if (targetId === '#friends') {
                loadFriends();
            } else if (targetId === '#requests') {
                loadFriendRequests();
            }
        });
    });
}

// 加载好友列表
function loadFriends() {
    fetch('/api/friends')
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                displayFriends(result.data);
            } else {
                showError('加载好友列表失败: ' + result.error);
            }
        })
        .catch(error => {
            console.error('加载好友列表失败:', error);
            showError('加载好友列表失败');
        });
}

// 显示好友列表
function displayFriends(friends) {
    const container = document.getElementById('friendsList');
    
    if (friends.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-user-friends"></i>
                <p>还没有好友，快去添加吧！</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = friends.map(friend => `
        <div class="friend-card d-flex align-items-center">
            <img src="${friend.avatar || '/static/images/default.jpg'}" 
                 alt="${friend.username}" 
                 class="friend-avatar me-3"
                 onerror="this.src='/static/images/default.jpg'">
            <div class="flex-grow-1">
                <h5 class="mb-1">${friend.username}</h5>
                <p class="text-muted mb-0 small">${friend.bio || '暂无简介'}</p>
            </div>
            <div>
                <button class="btn btn-sm btn-primary me-2" onclick="openChat('${friend.user_id}')">
                    <i class="fas fa-comment"></i> 发消息
                </button>
                <button class="btn btn-sm btn-danger" onclick="deleteFriend('${friend.user_id}', '${friend.username}')">
                    <i class="fas fa-user-times"></i> 删除
                </button>
            </div>
        </div>
    `).join('');
}

// 加载好友请求
function loadFriendRequests() {
    fetch('/api/friends/requests')
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                displayFriendRequests(result.data);
                updateRequestBadge(result.count);
            } else {
                showError('加载好友请求失败: ' + result.error);
            }
        })
        .catch(error => {
            console.error('加载好友请求失败:', error);
            showError('加载好友请求失败');
        });
}

// 显示好友请求
function displayFriendRequests(requests) {
    const container = document.getElementById('requestsList');
    
    if (requests.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-inbox"></i>
                <p>暂无待处理的好友请求</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = requests.map(req => `
        <div class="friend-card d-flex align-items-center">
            <img src="${req.requester_avatar || '/static/images/default.jpg'}" 
                 alt="${req.requester_username}" 
                 class="friend-avatar me-3"
                 onerror="this.src='/static/images/default.jpg'">
            <div class="flex-grow-1">
                <h5 class="mb-1">${req.requester_username}</h5>
                <p class="text-muted mb-0 small">请求时间: ${req.created_at}</p>
            </div>
            <div>
                <button class="btn btn-sm btn-success me-2" onclick="handleFriendRequest(${req.friendship_id}, 'accept')">
                    <i class="fas fa-check"></i> 接受
                </button>
                <button class="btn btn-sm btn-danger" onclick="handleFriendRequest(${req.friendship_id}, 'reject')">
                    <i class="fas fa-times"></i> 拒绝
                </button>
            </div>
        </div>
    `).join('');
}

// 更新请求徽章
function updateRequestBadge(count) {
    const badge = document.getElementById('requestBadge');
    if (count > 0) {
        badge.textContent = count;
        badge.style.display = 'inline-block';
    } else {
        badge.style.display = 'none';
    }
}

// 处理好友请求
function handleFriendRequest(friendshipId, action) {
    fetch(`/api/friends/request/${friendshipId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ action: action })
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            showSuccess(action === 'accept' ? '已接受好友请求' : '已拒绝好友请求');
            loadFriendRequests();
            loadFriends();
        } else {
            showError('处理失败: ' + result.error);
        }
    })
    .catch(error => {
        console.error('处理好友请求失败:', error);
        showError('处理失败');
    });
}

// 搜索用户
function searchUsers() {
    const keyword = document.getElementById('searchInput').value.trim();
    
    if (!keyword) {
        showError('请输入搜索关键词');
        return;
    }
    
    // 切换到搜索标签页
    const searchTab = document.getElementById('search-tab');
    const bsTab = new bootstrap.Tab(searchTab);
    bsTab.show();
    
    fetch(`/api/users/search?keyword=${encodeURIComponent(keyword)}`)
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                displaySearchResults(result.data);
            } else {
                showError('搜索失败: ' + result.error);
            }
        })
        .catch(error => {
            console.error('搜索失败:', error);
            showError('搜索失败');
        });
}

// 显示搜索结果
function displaySearchResults(users) {
    const container = document.getElementById('searchResults');
    
    if (users.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-search"></i>
                <p>没有找到相关用户</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = users.map(user => {
        let actionButton = '';
        const status = user.friendship_status;
        
        if (!status) {
            actionButton = `<button class="btn btn-sm btn-primary" onclick="sendFriendRequest('${user.user_id}', '${user.username}')">
                <i class="fas fa-user-plus"></i> 添加好友
            </button>`;
        } else if (status === 'pending') {
            actionButton = `<span class="badge badge-pending">待处理</span>`;
        } else if (status === 'accepted') {
            actionButton = `<span class="badge badge-accepted">已是好友</span>`;
        } else if (status === 'rejected') {
            actionButton = `<button class="btn btn-sm btn-primary" onclick="sendFriendRequest('${user.user_id}', '${user.username}')">
                <i class="fas fa-user-plus"></i> 重新添加
            </button>`;
        }
        
        return `
            <div class="friend-card d-flex align-items-center">
                <img src="${user.avatar || '/static/images/default.jpg'}" 
                     alt="${user.username}" 
                     class="friend-avatar me-3"
                     onerror="this.src='/static/images/default.jpg'">
                <div class="flex-grow-1">
                    <h5 class="mb-1">${user.username}</h5>
                    <p class="text-muted mb-0 small">${user.bio || '暂无简介'}</p>
                </div>
                <div>
                    ${actionButton}
                </div>
            </div>
        `;
    }).join('');
}

// 发送好友请求
function sendFriendRequest(userId, username) {
    if (!confirm(`确定要添加 ${username} 为好友吗？`)) {
        return;
    }
    
    fetch('/api/friends/request', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ user_id: userId })
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            showSuccess('好友请求已发送');
            // 重新搜索以更新状态
            const keyword = document.getElementById('searchInput').value.trim();
            if (keyword) {
                searchUsers();
            }
        } else {
            showError('发送失败: ' + result.error);
        }
    })
    .catch(error => {
        console.error('发送好友请求失败:', error);
        showError('发送失败');
    });
}

// 删除好友
function deleteFriend(friendId, username) {
    if (!confirm(`确定要删除好友 ${username} 吗？`)) {
        return;
    }
    
    fetch(`/api/friends/${friendId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            showSuccess('已删除好友');
            loadFriends();
        } else {
            showError('删除失败: ' + result.error);
        }
    })
    .catch(error => {
        console.error('删除好友失败:', error);
        showError('删除失败');
    });
}

// 打开聊天
function openChat(userId) {
    window.location.href = `/messages?user_id=${userId}`;
}

// 显示成功消息
function showSuccess(message) {
    const alert = document.createElement('div');
    alert.className = 'alert alert-success alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3';
    alert.style.zIndex = '9999';
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alert);
    setTimeout(() => alert.remove(), 3000);
}

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
