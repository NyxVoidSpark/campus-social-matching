// 页面加载时检查登录状态
document.addEventListener('DOMContentLoaded', function() {
    checkLoginStatus();
    setupEventListeners();
});

// 全局变量
let currentSearchType = 'all';

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
                document.getElementById('usernameDisplay').textContent = `欢迎，${result.data.username}`;
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
            const activities = data.success ? data.data : [];
            displayActivities(activities);
        })
        .catch(error => {
            console.error('获取活动数据失败:', error);
            const container = document.getElementById('activity-list');
            container.innerHTML = `
                <div class="col-12 error">
                    <p>❌ 加载失败，请刷新页面重试</p>
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
                        </p>
                        <p class="card-text small">
                            🕒 时间：${activity.time}<br>
                            📍 地点：${activity.location}
                        </p>
                        <div class="d-flex gap-2">
                            <button class="btn btn-primary flex-1" onclick="joinActivity(${activity.id})">
                                我要参加
                            </button>
                            <button class="btn btn-outline-warning flex-1" onclick="favoriteActivity(${activity.id})">
                                <<i class="fas fa-star"></</i>
                            </button>
                        </div>
                    </div>
                    <div class="card-footer text-muted">
                        参与人数：${activity.participants_count || 0}人
                    </div>
                </div>
            </div>
        `;
        container.innerHTML += card;
    });
}

// 按类型筛选活动
function filterActivities(type) {
    currentSearchType = type;
    fetch('/api/activities')
        .then(response => response.json())
        .then(data => {
            const allActivities = data.success ? data.data : [];
            let filtered = allActivities;

            if (type !== 'all') {
                filtered = allActivities.filter(activity => activity.type === type);
            }

            displayActivities(filtered);
        });
}

// 搜索活动
function searchActivities() {
    const keyword = document.getElementById('searchInput').value.trim();

    if (!keyword) {
        loadActivities();
        return;
    }

    // 显示搜索中状态
    const container = document.getElementById('activity-list');
    container.innerHTML = `
        <div class="col-12 text-center">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">搜索中...</span>
            </div>
            <p class="mt-3">正在搜索"${keyword}"...</p>
        </div>
    `;

    // 调用搜索API
    fetch(`/api/activities/search?keyword=${encodeURIComponent(keyword)}&type=${currentSearchType}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('搜索请求失败');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                if (data.count === 0) {
                    container.innerHTML = `
                        <div class="col-12">
                            <div class="alert alert-info">
                                <<i class="fas fa-search"></</i> 没有找到"${keyword}"相关的活动
                                <button class="btn btn-sm btn-outline-primary ms-3" onclick="loadActivities()">
                                    显示所有活动
                                </button>
                            </div>
                        </div>
                    `;
                } else {
                    container.innerHTML = `
                        <div class="col-12 mb-3">
                            <div class="alert alert-success d-flex justify-content-between align-items-center">
                                <span>
                                    <<i class="fas fa-check-circle"></</i> 找到 ${data.count} 个与"${keyword}"相关的活动
                                </span>
                                <button class="btn btn-sm btn-outline-secondary" onclick="clearSearch()">
                                    清除搜索
                                </button>
                            </div>
                        </div>
                    `;
                    displayActivities(data.data);
                }
            } else {
                container.innerHTML = `
                    <div class="col-12">
                        <div class="alert alert-danger">
                            <<i class="fas fa-exclamation-circle"></</i> 搜索失败：${data.error || '未知错误'}
                        </div>
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('搜索活动失败:', error);
            container.innerHTML = `
                <div class="col-12">
                    <div class="alert alert-danger">
                        <<i class="fas fa-exclamation-circle"></</i> 搜索失败，请刷新页面重试
                        <button class="btn btn-sm btn-outline-primary ms-3" onclick="loadActivities()">
                            返回活动列表
                        </button>
                    </div>
                </div>
            `;
        });
}

// 清空搜索
function clearSearch() {
    document.getElementById('searchInput').value = '';
    loadActivities();
}

// 报名活动
function joinActivity(activityId) {
    fetch(`/api/activities/${activityId}/join`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'}
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(data.message);
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

// 收藏活动
function favoriteActivity(activityId) {
    fetch(`/api/activities/${activityId}/favorite`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'}
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        loadActivities();
    })
    .catch(error => {
        console.error('收藏请求失败:', error);
        alert('操作失败，请重试');
    });
}

// 设置事件监听器（个人中心页面用）
function setupEventListeners() {
    // 个人简介字数统计
    const bioElement = document.getElementById('bio');
    if (bioElement) {
        bioElement.addEventListener('input', function() {
            const countElement = document.getElementById('bioCount');
            if (countElement) {
                countElement.textContent = this.value.length;
            }
        });
    }

    // 详细资料表单提交
    const detailedForm = document.getElementById('detailedProfileForm');
    if (detailedForm) {
        detailedForm.addEventListener('submit', function(e) {
            e.preventDefault();

            const data = {
                real_name: document.getElementById('real_name').value,
                student_id: document.getElementById('student_id').value,
                major: document.getElementById('major').value,
                grade: document.getElementById('grade').value,
                gender: document.getElementById('gender').value,
                phone: document.getElementById('phone').value,
                email: document.getElementById('email').value,
                bio: document.getElementById('bio').value
            };

            fetch('/api/user/profile/detailed', {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(result => {
                const messageDiv = document.getElementById('detailedProfileMessage');
                if (result.success) {
                    messageDiv.innerHTML = `
                        <div class="alert alert-success">
                            <<i class="fas fa-check-circle"></</i> ${result.message}
                        </div>
                    `;
                    loadDetailedProfile();
                } else {
                    messageDiv.innerHTML = `
                        <div class="alert alert-danger">
                            <<i class="fas fa-exclamation-circle"></</i> ${result.error}
                        </div>
                    `;
                }

                setTimeout(() => {
                    if (messageDiv) messageDiv.innerHTML = '';
                }, 3000);
            })
            .catch(error => {
                console.error('更新详细资料失败:', error);
                const messageDiv = document.getElementById('detailedProfileMessage');
                if (messageDiv) {
                    messageDiv.innerHTML = `
                        <div class="alert alert-danger">
                            <<i class="fas fa-exclamation-circle"></</i> 更新失败，请重试
                        </div>
                    `;
                }
            });
        });
    }

    // 个人资料表单提交（邮箱更新）
    const profileForm = document.getElementById('profileForm');
    if (profileForm) {
        profileForm.addEventListener('submit', function(e) {
            e.preventDefault();

            const data = { email: document.getElementById('email').value };

            fetch('/api/user/profile', {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(result => {
                const messageDiv = document.getElementById('profileMessage');
                if (result.success) {
                    messageDiv.innerHTML = `
                        <div class="alert alert-success">
                            <<i class="fas fa-check-circle"></</i> ${result.message}
                        </div>
                    `;
                    loadUserProfile();
                } else {
                    messageDiv.innerHTML = `
                        <div class="alert alert-danger">
                            <<i class="fas fa-exclamation-circle"></</i> ${result.error}
                        </div>
                    `;
                }

                setTimeout(() => {
                    if (messageDiv) messageDiv.innerHTML = '';
                }, 3000);
            })
            .catch(error => {
                console.error('更新个人资料失败:', error);
                const messageDiv = document.getElementById('profileMessage');
                if (messageDiv) {
                    messageDiv.innerHTML = `
                        <div class="alert alert-danger">
                            <<i class="fas fa-exclamation-circle"></</i> 更新失败，请重试
                        </div>
                    `;
                }
            });
        });
    }
}

// 个人中心相关加载函数
function loadUserProfile() {
    fetch('/api/user/profile')
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                const data = result.data;
                updateBasicProfile(data);
            }
        })
        .catch(error => {
            console.error('加载用户资料失败:', error);
        });
}

function loadDetailedProfile() {
    fetch('/api/user/profile/detailed')
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                const data = result.data;
                updateDetailedProfile(data);
                updateProfileCompletion(data);
            } else {
                console.error('加载详细资料失败:', result.error);
            }
        })
        .catch(error => {
            console.error('获取详细资料失败:', error);
        });
}

function loadJoinedActivities() {
    fetch('/api/user/joined-activities')
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                displayJoinedActivities(result.data);
                const loadingElement = document.getElementById('joinedLoading');
                if (loadingElement) {
                    loadingElement.style.display = 'none';
                }
            }
        })
        .catch(error => {
            console.error('加载已参与活动失败:', error);
            const loadingElement = document.getElementById('joinedLoading');
            if (loadingElement) {
                loadingElement.innerHTML = '<p class="text-danger">加载失败，请刷新页面重试</p>';
            }
        });
}

function loadFavorites() {
    fetch('/api/user/favorites')
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                displayFavorites(result.data);
                const loadingElement = document.getElementById('favoritesLoading');
                if (loadingElement) {
                    loadingElement.style.display = 'none';
                }
            }
        })
        .catch(error => {
            console.error('加载收藏活动失败:', error);
            const loadingElement = document.getElementById('favoritesLoading');
            if (loadingElement) {
                loadingElement.innerHTML = '<p class="text-danger">加载失败，请刷新页面重试</p>';
            }
        });
}

// 个人中心渲染函数
function updateBasicProfile(data) {
    document.getElementById('usernameDisplay').textContent = data.username;
    document.getElementById('userEmail').textContent = data.email || '未设置';
    document.getElementById('email').value = data.email || '';
    document.getElementById('joinDate').textContent = data.created_at || '';
    document.getElementById('joinDateSettings').value = data.created_at || '';
    document.getElementById('joinedCount').textContent = data.stats?.activities_joined || 0;
    document.getElementById('totalActivities').textContent = data.stats?.total_activities || 0;
    document.getElementById('favoritesCount').textContent = data.stats?.favorites_count || 0;

    // 计算注册天数
    if (data.created_at) {
        const createdDate = new Date(data.created_at);
        const today = new Date();
        const diffTime = Math.abs(today - createdDate);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        document.getElementById('accountDays').textContent = diffDays;
    }

    // 更新头像
    if (data.avatar) {
        document.getElementById('avatarPreview').src = data.avatar;
        document.getElementById('avatarPreview').style.display = 'block';
        document.getElementById('avatarIcon').style.display = 'none';
        document.getElementById('avatarPreviewDetailed').src = data.avatar;
    }
}

function updateDetailedProfile(data) {
    document.getElementById('real_name').value = data.real_name || '';
    document.getElementById('student_id').value = data.student_id || '';
    document.getElementById('major').value = data.major || '';
    document.getElementById('grade').value = data.grade || '';
    document.getElementById('gender').value = data.gender || '';
    document.getElementById('phone').value = data.phone || '';
    document.getElementById('email').value = data.email || '';
    document.getElementById('bio').value = data.bio || '';
    document.getElementById('bioCount').textContent = (data.bio || '').length;

    // 更新账户信息
    document.getElementById('infoUsername').textContent = data.username || '';
    document.getElementById('infoUserId').textContent = data.user_id || '';
    document.getElementById('infoEmail').textContent = data.email || '';
    document.getElementById('infoCreatedAt').textContent = data.created_at || '';

    // 更新顶部信息
    document.getElementById('userMajor').textContent = data.major ? `专业: ${data.major}` : '';
    document.getElementById('userGrade').textContent = data.grade ? `年级: ${data.grade}` : '';
    document.getElementById('userBio').textContent = data.bio || '';

    // 更新头像
    if (data.avatar && data.avatar !== '/static/avatars/default.jpg') {
        document.getElementById('avatarPreview').src = data.avatar;
        document.getElementById('avatarPreview').style.display = 'block';
        document.getElementById('avatarIcon').style.display = 'none';
        document.getElementById('avatarPreviewDetailed').src = data.avatar;
    }
}

function updateProfileCompletion(profile) {
    const checklist = [
        { field: 'real_name', text: '真实姓名', weight: 20 },
        { field: 'email', text: '邮箱地址', weight: 20 },
        { field: 'major', text: '专业信息', weight: 20 },
        { field: 'phone', text: '联系方式', weight: 15 },
        { field: 'bio', text: '个人简介', weight: 15 },
        { field: 'avatar', text: '个人头像', weight: 10 }
    ];

    let totalScore = 0;
    const container = document.getElementById('profileChecklist');
    if (!container) return;

    container.innerHTML = '';

    checklist.forEach(item => {
        const isCompleted = profile[item.field] &&
            (item.field === 'avatar' ? profile[item.field] !== '/static/avatars/default.jpg' : profile[item.field].trim() !== '');

        if (isCompleted) totalScore += item.weight;

        const itemDiv = document.createElement('div');
        itemDiv.className = `completion-item ${isCompleted ? 'completed' : ''}`;
        itemDiv.innerHTML = `
            <div class="d-flex justify-content-between align-items-center">
                <span>${item.text}</span>
                <<i class="fas fa-${isCompleted ? 'check' : 'times'}"></</i>
            </div>
            <div class="progress mt-1" style="height: 4px;">
                <div class="progress-bar ${isCompleted ? 'bg-success' : 'bg-light'}"
                     style="width: ${item.weight}%"></div>
            </div>
        `;
        container.appendChild(itemDiv);
    });

    // 更新进度条和百分比
    const percentage = Math.round((totalScore / 100) * 100);
    const completionElement = document.getElementById('profileCompletion');
    const completionBar = document.getElementById('completionBar');

    if (completionElement) completionElement.textContent = `${percentage}%`;
    if (completionBar) {
        completionBar.style.width = `${percentage}%`;
        completionBar.className = `progress-bar ${percentage >= 80 ? 'bg-success' : percentage >= 50 ? 'bg-warning' : 'bg-danger'}`;
    }
}

function displayJoinedActivities(activities) {
    const container = document.getElementById('joinedActivitiesList');
    if (!container) return;

    container.innerHTML = '';

    if (activities.length === 0) {
        container.innerHTML = `
            <div class="col-12">
                <div class="alert alert-warning">
                    <<i class="fas fa-info-circle"></</i>
                    您还没有参与任何活动，快去首页看看吧！
                    <a href="/" class="btn btn-sm btn-outline-primary ms-2">浏览活动</a>
                </div>
            </div>
        `;
        return;
    }

    activities.forEach(activity => {
        const card = `
            <div class="col-md-6 mb-3">
                <div class="card activity-card">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start">
                            <h5 class="card-title mb-1">${activity.title}</h5>
                            <span class="badge badge-custom">${activity.type}</span>
                        </div>
                        <p class="card-text text-muted small mb-2">
                            <<i class="fas fa-clock"></</i> ${activity.time}<br>
                            <<i class="fas fa-map-marker-alt"></</i> ${activity.location}
                        </p>
                        <div class="d-flex justify-content-between align-items-center">
                            <small class="text-muted">
                                <<i class="fas fa-users"></</i> ${activity.participants.length}人参与
                            </small>
                            <button class="btn btn-outline-danger btn-sm" onclick="leaveActivity(${activity.id})">
                                <<i class="fas fa-times"></</i> 取消报名
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        container.innerHTML += card;
    });
}

function displayFavorites(activities) {
    const container = document.getElementById('favoritesList');
    if (!container) return;

    if (activities.length === 0) {
        container.innerHTML = `
            <div class="col-12">
                <div class="alert alert-warning">
                    <<i class="fas fa-info-circle"></</i>
                    您还没有收藏任何活动
                    <a href="/" class="btn btn-sm btn-outline-primary ms-2">去收藏活动</a>
                </div>
            </div>
        `;
        return;
    }

    container.innerHTML = '';
    activities.forEach(activity => {
        const card = `
            <div class="col-md-6 mb-3">
                <div class="card activity-card">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start">
                            <h5 class="card-title mb-1">${activity.title}</h5>
                            <span class="badge badge-custom">${activity.type}</span>
                        </div>
                        <p class="card-text text-muted small mb-2">
                            <<i class="fas fa-clock"></</i> ${activity.time}<br>
                            <<i class="fas fa-map-marker-alt"></</i> ${activity.location}
                        </p>
                        <div class="d-flex justify-content-between align-items-center">
                            <small class="text-muted">
                                <<i class="fas fa-users"></</i> ${activity.participants.length}人参与
                            </small>
                            <button class="btn btn-outline-warning btn-sm" onclick="unfavoriteActivity(${activity.id})">
                                <<i class="fas fa-star"></</i> 取消收藏
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        container.innerHTML += card;
    });
}

// 取消报名
function leaveActivity(activityId) {
    if (!confirm('确定要取消报名吗？')) return;

    fetch(`/api/activities/${activityId}/leave`, { method: 'POST' })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                alert(result.message);
                loadJoinedActivities();
                loadUserProfile();
            } else {
                alert(result.error);
            }
        })
        .catch(error => {
            console.error('取消报名失败:', error);
            alert('操作失败，请重试');
        });
}

// 取消收藏
function unfavoriteActivity(activityId) {
    if (!confirm('确定要取消收藏吗？')) return;

    fetch(`/api/activities/${activityId}/favorite`, { method: 'POST' })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                alert(result.message);
                loadFavorites();
                loadUserProfile();
            } else {
                alert(result.error);
            }
        })
        .catch(error => {
            console.error('取消收藏失败:', error);
            alert('操作失败，请重试');
        });
}

// 头像预览（个人中心用）
function previewAvatar(input) {
    if (input.files && input.files[0]) {
        const file = input.files[0];

        // 检查文件大小（2MB限制）
        if (file.size > 2 * 1024 * 1024) {
            alert('文件太大，请选择小于2MB的图片');
            return;
        }

        // 检查文件类型
        if (!file.type.match('image.*')) {
            alert('请选择图片文件（JPG/PNG格式）');
            return;
        }

        const reader = new FileReader();
        reader.onload = function(e) {
            document.getElementById('avatarPreview').src = e.target.result;
            document.getElementById('avatarPreview').style.display = 'block';
            document.getElementById('avatarIcon').style.display = 'none';
            document.getElementById('avatarPreviewDetailed').src = e.target.result;
        };
        reader.readAsDataURL(file);
    }
}

// 上传头像（需额外实现后端存储逻辑，此处仅为前端示例）
function uploadAvatar() {
    alert('请到个人中心页面上传头像');
}
// 修改密码（前端示例，后端需额外实现）
function updatePassword() {
    const currentPassword = document.getElementById('currentPassword').value;
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;

    if (!currentPassword || !newPassword || !confirmPassword) {
        document.getElementById('passwordMessage').innerHTML = `
            <div class="alert alert-danger">请填写所有字段</div>
        `;
        return;
    }

    if (newPassword !== confirmPassword) {
        document.getElementById('passwordMessage').innerHTML = `
            <div class="alert alert-danger">两次输入的新密码不一致</div>
        `;
        return;
    }

    if (newPassword.length < 8) {
        document.getElementById('passwordMessage').innerHTML = `
            <div class="alert alert-danger">密码长度至少8位</div>
        `;
        return;
    }

    // 后端需实现修改密码接口，此处仅为示例
    alert('修改密码功能需后端额外实现，可基于用户ID更新密码哈希值');

    // 关闭模态框
    const modalElement = document.getElementById('changePasswordModal');
    if (modalElement) {
        const modal = bootstrap.Modal.getInstance(modalElement);
        if (modal) modal.hide();
    }
}