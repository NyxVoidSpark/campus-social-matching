// 页面加载完成后加载活动数据
document.addEventListener('DOMContentLoaded', function() {
    loadActivities();
});
// 页面加载时检查登录状态
document.addEventListener('DOMContentLoaded', function() {
    checkLoginStatus();
});

// 检查登录状态
function checkLoginStatus() {
    fetch('/api/current-user')
        .then(response => {
            if (response.status === 401) {
                // 未登录，跳转到登录页
                window.location.href = '/login';
                return;
            }
            return response.json();
        })
        .then(result => {
            if (result.success) {
                // 显示用户名
                document.getElementById('usernameDisplay').textContent = `欢迎，${result.data.username}`;
                // 加载活动列表
                loadActivities();
            }
        })
        .catch(error => {
            console.error('检查登录状态失败:', error);
            window.location.href = '/login';
        });
}

// 登出功能
function logout() {
    fetch('/api/logout', { method: 'POST' })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                window.location.href = '/login';
            }
        });
}

// 保留原有活动加载、筛选、报名等功能
function loadActivities() {
    fetch('/api/activities')
        .then(response => response.json())
        .then(data => {
            const activities = data.success ? data.data : [];
            displayActivities(activities);
        })
        .catch(error => {
            console.error('获取活动数据失败:', error);
            const container = document.getElementById('activity-list');
            container.innerHTML = `
                <div class="col-12 error">
                    <p>❌ 加载失败，请刷新页面重试</p >
                </div>
            `;
        });
}
// 加载所有活动数据
function loadActivities() {
    fetch('/api/activities')
        .then(response => {
            if (!response.ok) {
                throw new Error('网络请求失败');
            }
            return response.json();
        })
        .then(data => {
            // 适配整合后的API响应格式
            const activities = data.success ? data.data : [];
            displayActivities(activities);
        })
        .catch(error => {
            console.error('获取活动数据失败:', error);
            const container = document.getElementById('activity-list');
            container.innerHTML = `
                <div class="col-12 error">
                    <p>❌ 加载失败，请刷新页面重试</p >
                </div>
            `;
        });
}

// 渲染活动列表
function displayActivities(activities) {
    const container = document.getElementById('activity-list');
    container.innerHTML = '';

    if (activities.length === 0) {
        container.innerHTML = `
            <div class="col-12">
                <div class="alert alert-warning text-center p-3">
                    📢 暂无活动数据，敬请期待
                </div>
            </div>
        `;
        return;
    }

    // 循环渲染活动卡片
    activities.forEach(activity => {
        const card = `
            <div class="col-md-4">
                <div class="card h-100">
                    <div class="card-body">
                        <h5 class="card-title">${activity.title}</h5>
                        <p class="card-text">
                            <span class="badge bg-secondary">${activity.type}</span>
                        </p >
                        <p class="card-text small">
                            🕒 时间：${activity.time}<br>
                            📍 地点：${activity.location}
                        </p >
                        <button class="btn btn-primary w-100" onclick="joinActivity(${activity.id})">
                            我要参加
                        </button>
                    </div>
                    <div class="card-footer text-muted">
                        参与人数：${activity.participants ? activity.participants.length : 0}人
                    </div>
                </div>
            </div>
        `;
        container.innerHTML += card;
    });
}

// 按类型筛选活动
function filterActivities(type) {
    fetch('/api/activities')
        .then(response => response.json())
        .then(data => {
            const allActivities = data.success ? data.data : [];
            let filtered = allActivities;

            // 如果不是"全部活动"，则筛选对应类型
            if (type !== 'all') {
                filtered = allActivities.filter(activity => activity.type === type);
            }

            displayActivities(filtered);
        });
}

// 报名参加活动
function joinActivity(activityId) {
    // 模拟用户信息（实际项目中应从登录状态获取）
    const user = { id: 1, name: "当前用户" };

    fetch(`/api/activities/${activityId}/join`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ user: user })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('报名失败');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            alert(data.message);
            // 重新加载活动列表，更新参与人数
            loadActivities();
        } else {
            alert(data.error);
        }
    })
    .catch(error => {
        console.error('报名请求失败:', error);
        alert('报名失败，请重试');
    });
}