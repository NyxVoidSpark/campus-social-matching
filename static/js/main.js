// 页面加载时检查登录状态
document.addEventListener('DOMContentLoaded', function() {
    checkLoginStatus();
    setupEventListeners();
    initPostsUI();
    initActivityForm();
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
        const isFavorited = !!activity.is_favorited;
        const starClass = isFavorited ? 'fa-solid fa-star text-warning' : 'fa-regular fa-star text-warning';
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
                            <button class="btn btn-outline-warning flex-1" onclick="favoriteActivity(${activity.id})" aria-label="收藏活动">
                                <i class="${starClass}"></i>
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
    applyAdvancedFilters();
}
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
                                <i class="fas fa-search"></i> 没有找到"${keyword}"相关的活动
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
                                    <i class="fas fa-check-circle"></i> 找到 ${data.count} 个与"${keyword}"相关的活动
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
                            <i class="fas fa-exclamation-circle"></i> 搜索失败：${data.error || '未知错误'}
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
                        <i class="fas fa-exclamation-circle"></i> 搜索失败，请刷新页面重试
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
        headers: {'Content-Type': 'application/json'},
        credentials: 'include'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            loadActivities(); // 刷新列表以同步星星点亮状态
        } else {
            alert(data.error || '操作失败，请重试');
        }
    })
    .catch(error => {
        console.error('收藏请求失败:', error);
        alert('操作失败，请重试');
    });
}

// 发布活动表单（首页用）
function initActivityForm() {
    const form = document.getElementById('activityForm');
    const msg = document.getElementById('activityFormMsg');
    if (!form) return;

    form.addEventListener('submit', function(e) {
        e.preventDefault();
        if (msg) msg.innerHTML = '<div class="alert alert-info">正在发布活动...</div>';

        const payload = {
            title: document.getElementById('activityTitle')?.value || '',
            type: document.getElementById('activityType')?.value || '',
            time: document.getElementById('activityTime')?.value || '',
            location: document.getElementById('activityLocation')?.value || '',
            tags: document.getElementById('activityTags')?.value || '',
            description: document.getElementById('activityDesc')?.value || ''
        };

        fetch('/api/activities', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
            credentials: 'include'
        })
        .then(r => r.json().then(j => ({ ok: r.ok, body: j })))
        .then(res => {
            if (res.body?.success) {
                if (msg) msg.innerHTML = '<div class="alert alert-success">活动发布成功！</div>';
                form.reset();
                loadActivities();
                // 发布后立刻在“我的首页”看到热门活动
                setTimeout(() => { window.location.href = '/personal_home'; }, 600);
            } else {
                if (msg) msg.innerHTML = `<div class="alert alert-danger">发布失败：${res.body?.error || '未知错误'}</div>`;
            }
        })
        .catch(err => {
            console.error('发布活动失败:', err);
            if (msg) msg.innerHTML = '<div class="alert alert-danger">发布失败，请重试</div>';
        });
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
                            <i class="fas fa-check-circle"></i> ${result.message}
                        </div>
                    `;
                    loadDetailedProfile();
                } else {
                    messageDiv.innerHTML = `
                        <div class="alert alert-danger">
                            <i class="fas fa-exclamation-circle"></i> ${result.error}
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
                            <i class="fas fa-exclamation-circle"></i> 更新失败，请重试
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
                            <i class="fas fa-check-circle"></i> ${result.message}
                        </div>
                    `;
                    loadUserProfile();
                } else {
                    messageDiv.innerHTML = `
                        <div class="alert alert-danger">
                            <i class="fas fa-exclamation-circle"></i> ${result.error}
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
                            <i class="fas fa-exclamation-circle"></i> 更新失败，请重试
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

// ------------------- 帖子与小组相关功能 -------------------
function initPostsUI(){
    // 仅在首页存在发布表单时初始化
    if(!document.getElementById('postForm')) return;

    // 加载模板与分类
    fetch('/api/post-templates')
        .then(r => r.json())
        .then(res => {
            if(res.success){
                const categories = res.categories || Object.keys(res.data || {});
                const sel = document.getElementById('postCategory');
                sel.innerHTML = '<option value="">请选择分类</option>';
                categories.forEach(c => {
                    const o = document.createElement('option'); o.value = c; o.textContent = c; sel.appendChild(o);
                });

                // 如果页面存在顶部的活动类型按钮区域，则用相同分类填充它
                const activityBtnGroup = document.getElementById('activityTypeButtons');
                if(activityBtnGroup){
                    activityBtnGroup.innerHTML = '';
                    // 全部按钮
                    const allBtn = document.createElement('button');
                    allBtn.type = 'button';
                    allBtn.className = 'btn btn-primary active';
                    allBtn.textContent = '全部';
                    allBtn.addEventListener('click', function(){
                        // 视觉高亮
                        Array.from(activityBtnGroup.children).forEach(b=>b.classList.remove('active'));
                        this.classList.add('active');
                        filterActivities('all');
                        loadPostsList();
                    });
                    activityBtnGroup.appendChild(allBtn);

                    // 每个分类对应一个按钮（点击既筛选活动也筛选信息流）
                    categories.forEach(cat => {
                        const btn = document.createElement('button');
                        btn.type = 'button';
                        btn.className = 'btn btn-outline-primary';
                        btn.textContent = cat;
                        btn.addEventListener('click', function(){
                            Array.from(activityBtnGroup.children).forEach(b=>b.classList.remove('active'));
                            this.classList.add('active');
                            filterActivities(cat);
                            loadPostsList(cat);
                        });
                        activityBtnGroup.appendChild(btn);
                    });
                }

                // 当分类改变时渲染模板字段
                sel.addEventListener('change', function(){ renderTemplateFields(res.data[this.value]); });
            }
            // 首次加载帖子列表
            loadPostsList();
        }).catch(err=>{ console.error('加载模板失败', err); loadPostsList(); });

    // 绑定检查相似按钮
    const chk = document.getElementById('checkSimilarBtn');
    if(chk) chk.addEventListener('click', function(){ checkSimilar(false); });

    // 绑定发布表单提交
    const form = document.getElementById('postForm');
    form.addEventListener('submit', function(e){
        e.preventDefault();
        submitPost();
    });

    // 绑定创建小组
    const createBtn = document.getElementById('createGroupBtn');
    if(createBtn) createBtn.addEventListener('click', createGroup);
}

function renderTemplateFields(template){
    const container = document.getElementById('postMetadata');
    container.innerHTML = '';
    if(!template || !template.fields) return;
    template.fields.forEach(f => {
        let html = '';
        if(f.type === 'checkbox'){
            html = `<div class="form-check mb-2"><input class="form-check-input" type="checkbox" id="meta_${f.name}" name="${f.name}"><label class="form-check-label" for="meta_${f.name}">${f.label}</label></div>`;
        } else {
            html = `<div class="mb-2"><label class="form-label">${f.label}</label><input class="form-control" id="meta_${f.name}" name="${f.name}" type="${f.type}"></div>`;
        }
        container.innerHTML += html;
    });
}

function collectMetadata(){
    const container = document.getElementById('postMetadata');
    const inputs = container.querySelectorAll('input');
    const data = {};
    inputs.forEach(inp => {
        if(inp.type === 'checkbox') data[inp.name.replace(/^meta_/, '')] = inp.checked;
        else data[inp.name.replace(/^meta_/, '')] = inp.value;
    });
    return data;
}

function checkSimilar(showAlert){
    const title = document.getElementById('postTitle').value || '';
    const content = document.getElementById('postContent').value || '';
    if(!title && !content){ if(showAlert) alert('请填写标题或内容后再检查相似'); return; }
    fetch(`/api/posts/similar?title=${encodeURIComponent(title)}&content=${encodeURIComponent(content)}`)
        .then(r=>r.json()).then(res=>{
            if(res.success && res.count>0){
                const msg = res.data.map(d=>`${d.post.title} (score:${(d.score*100).toFixed(0)}%)`).join('\n');
                if(showAlert) alert('发现可能相似的信息:\n'+msg);
                const msgDiv = document.getElementById('postFormMsg');
                if(msgDiv) msgDiv.innerHTML = `<div class="alert alert-warning">检测到相似信息，建议先查看或合并：<pre style="white-space:pre-wrap">${msg}</pre></div>`;
            } else {
                const msgDiv = document.getElementById('postFormMsg'); if(msgDiv) msgDiv.innerHTML = '<div class="alert alert-success">未检测到明显重复</div>';
            }
        }).catch(err=>{ console.error('相似检测失败', err); });
}

function submitPost(){
    const title = document.getElementById('postTitle').value || '';
    const category = document.getElementById('postCategory').value || '';
    const content = document.getElementById('postContent').value || '';
    const tags = document.getElementById('postTags').value || '';
    const metadata = collectMetadata();
    const files = document.getElementById('postFiles').files;
    const fd = new FormData();
    fd.append('title', title);
    fd.append('category', category);
    fd.append('content', content);
    fd.append('tags', tags);
    fd.append('metadata', JSON.stringify(metadata));
    for(let i=0;i<files.length;i++) fd.append('files', files[i]);

    // 显示正在发布状态
    const msgDiv = document.getElementById('postFormMsg');
    msgDiv.innerHTML = '<div class="alert alert-info">正在发布中...</div>';

    // 添加完整的调试信息
    console.log('提交帖子数据:', {
        title: title,
        category: category,
        contentLength: content.length,
        tags: tags
    });

    fetch('/api/posts', {
        method: 'POST',
        body: fd,
        // 不要设置 Content-Type，让浏览器自动设置 multipart/form-data
    })
    .then(async response => {
        console.log('响应状态:', response.status, response.statusText);

        // 先尝试获取原始响应文本
        const text = await response.text();
        console.log('原始响应文本前200字符:', text.substring(0, 200));

        // 检查是否是 HTML 页面
        if (text.trim().startsWith('<!DOCTYPE') || text.trim().startsWith('<!doctype')) {
            console.error('后端返回了HTML页面而不是JSON');

            // 检查是否包含登录重定向
            if (text.includes('login') || text.includes('登录')) {
                return {
                    status: 401,
                    body: { error: '用户未登录或会话已过期' }
                };
            }

            // 尝试解析 HTML 中的错误信息
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = text;
            const errorText = tempDiv.textContent || '服务器返回了错误页面';

            return {
                status: 500,
                body: { error: `服务器错误: ${errorText.substring(0, 100)}...` }
            };
        }

        // 尝试解析为 JSON
        try {
            const json = JSON.parse(text);
            return {
                status: response.status,
                body: json
            };
        } catch (e) {
            console.error('解析JSON失败:', e);
            return {
                status: response.status,
                body: { error: `响应格式错误: ${text.substring(0, 100)}...` }
            };
        }
    })
    .then(res => {
        console.log('处理后响应:', res);

        if (res.status === 201) {
            msgDiv.innerHTML = '<div class="alert alert-success">发布成功，等待审核</div>';
            document.getElementById('postForm').reset();
            loadPostsList();
        }
        else if (res.status === 409) {
            msgDiv.innerHTML = `<div class="alert alert-warning">${res.body.error || '可能存在重复'}<br><small>请先检查原帖</small></div>`;
        }
        else if (res.status === 401) {
            msgDiv.innerHTML = `<div class="alert alert-danger">请先登录再发布帖子</div>`;
            setTimeout(() => {
                window.location.href = '/login';
            }, 2000);
        }
        else {
            msgDiv.innerHTML = `<div class="alert alert-danger">发布失败：${res.body.error || `状态码 ${res.status}`}</div>`;
        }
    })
    .catch(err => {
        console.error('发布失败:', err);
        msgDiv.innerHTML = '<div class="alert alert-danger">网络错误，请稍后再试</div>';
    });
}

function loadPostsList(category){
    let url = '/api/posts';
    if(category) url += `?category=${encodeURIComponent(category)}`;
    fetch(url)
        .then(r=>r.json())
        .then(res=>{
            const list = document.getElementById('postsList');
            list.innerHTML = '';
            if(!res.success || res.count===0){ list.innerHTML = '<div class="text-muted p-3">暂无信息</div>'; return; }
            res.data.forEach(p=>{
                const item = document.createElement('a');
                item.className = 'list-group-item list-group-item-action';
                item.href = 'javascript:void(0);';
                const badge = p.is_official ? '<span class="badge bg-danger ms-2">官方</span>' : '';
                item.innerHTML = `<div class="d-flex justify-content-between"><div><strong>${escapeHtml(p.title)}</strong> ${badge}<div class="small text-muted">${escapeHtml(p.category)} · ${escapeHtml(p.created_at)}</div></div></div><div class="mt-2">${escapeHtml(p.content || '')}</div>`;
                item.addEventListener('click', function(){ showPost(p.id); });
                list.appendChild(item);
            });
        }).catch(err=>{ console.error('加载帖子失败', err); });
}

function showPost(postId){
    fetch(`/api/posts/${postId}`)
        .then(r=>r.json())
        .then(res=>{
            if(!res.success){ alert('帖子不存在或已删除'); return; }
            const p = res.data;
            document.getElementById('postDetailTitle').textContent = p.title;
            const body = document.getElementById('postDetailBody');
            let html = `<div class="mb-2 small text-muted">${escapeHtml(p.category)} · ${escapeHtml(p.created_at)}</div>`;
            html += `<div class="mb-3">${escapeHtml(p.content || '')}</div>`;
            if(p.media && p.media.length){
                html += '<div class="mb-2">';
                p.media.forEach(m=>{ html += `<div><a href="${m.url}" target="_blank">${escapeHtml(m.filename)}</a></div>`; });
                html += '</div>';
            }
            html += `<div id="postInteractions_${p.id}" class="mt-3"><button class="btn btn-sm btn-outline-primary me-2" onclick="reactPost(${p.id}, 'like')">点赞</button><button class="btn btn-sm btn-outline-secondary me-2" onclick="reactPost(${p.id}, 'favorite')">收藏</button></div>`;
            html += `<div class="mt-3"><h6>评论</h6><div id="commentsContainer_${p.id}">加载中...</div><div class="mt-2"><textarea id="newComment_${p.id}" class="form-control" rows="3" placeholder="写评论..."></textarea><div class="d-flex gap-2 mt-2"><button class="btn btn-sm btn-primary" onclick="submitComment(${p.id}, null)">发表评论</button></div></div></div>`;
            body.innerHTML = html;
            const modalEl = document.getElementById('postDetailModal');
            const modal = new bootstrap.Modal(modalEl);
            modal.show();
            // 加载评论
            loadComments(postId);
        }).catch(err=>{ console.error('获取帖子详情失败', err); alert('获取帖子详情失败'); });
}

function reactPost(postId, type){
    fetch(`/api/posts/${postId}/react`, { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({type}) })
        .then(r=>r.json().then(j=>({status:r.status, body:j}))).then(res=>{
            if(res.status===401){ alert('请先登录后再互动'); window.location.href='/login'; return; }
            if(res.status===200){ alert('操作成功'); } else { alert(res.body.error || '互动失败'); }
        }).catch(err=>{ console.error('互动失败', err); alert('互动失败'); });
}

function loadComments(postId){
    fetch(`/api/posts/${postId}/comments`)
        .then(r=>r.json())
        .then(res=>{
            const container = document.getElementById(`commentsContainer_${postId}`);
            if(!container) return;
            if(!res.success || res.count===0){ container.innerHTML = '<div class="text-muted">暂无评论</div>'; return; }
            function renderList(list, depth){
                let html = '';
                list.forEach(c=>{
                    html += `<div class="mb-2" style="margin-left:${(depth||0)*18}px; padding:6px; border-left:1px solid #eee;">`;
                    html += `<div class="small text-muted">用户:${escapeHtml(c.author_id)} · ${escapeHtml(c.created_at)}</div>`;
                    html += `<div class="mt-1">${escapeHtml(c.content)}</div>`;
                    html += `<div class="mt-1"><button class="btn btn-sm btn-link" onclick="promptReply(${postId}, ${c.id})">回复</button></div>`;
                    if(c.children && c.children.length){ html += renderList(c.children, (depth||0)+1); }
                    html += `</div>`;
                });
                return html;
            }
            container.innerHTML = renderList(res.data, 0);
        }).catch(err=>{ console.error('加载评论失败', err); const container = document.getElementById(`commentsContainer_${postId}`); if(container) container.innerHTML = '<div class="text-danger">加载评论失败</div>'; });
}

function submitComment(postId, parentId){
    const ta = document.getElementById(`newComment_${postId}`);
    if(!ta) return;
    const content = ta.value.trim();
    if(!content){ alert('请填写评论内容'); return; }
    fetch(`/api/posts/${postId}/comments`, { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({content, parent_id: parentId}) })
        .then(r=>r.json().then(j=>({status:r.status, body:j}))).then(res=>{
            if(res.status===401){ alert('请先登录'); window.location.href='/login'; return; }
            if(res.status===201){ ta.value=''; loadComments(postId); }
            else { alert(res.body.error || '发表评论失败'); }
        }).catch(err=>{ console.error('发表评论失败', err); alert('发表评论失败'); });
}

function promptReply(postId, parentId){
    const reply = prompt('输入回复内容：');
    if(reply && reply.trim()){
        // 为快速实现直接 POST
        fetch(`/api/posts/${postId}/comments`, { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({content: reply.trim(), parent_id: parentId}) })
            .then(r=>r.json().then(j=>({status:r.status, body:j}))).then(res=>{
                if(res.status===201) loadComments(postId);
                else if(res.status===401){ alert('请先登录'); window.location.href='/login'; }
                else alert(res.body.error || '回复失败');
            }).catch(err=>{ console.error('回复失败', err); alert('回复失败'); });
    }
}

function createGroup(){
    const name = document.getElementById('groupName').value.trim();
    const desc = document.getElementById('groupDesc').value.trim();
    const msg = document.getElementById('groupMsg');
    if(!name){ msg.innerHTML = '<div class="text-danger">请填写小组名称</div>'; return; }
    fetch('/api/groups', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({name, description: desc}) })
        .then(r=>r.json().then(j=>({status:r.status, body:j}))).then(res=>{
            if(res.status===201){ msg.innerHTML = '<div class="text-success">小组创建成功</div>'; document.getElementById('groupName').value=''; document.getElementById('groupDesc').value=''; }
            else if(res.status===401){ alert('请先登录以创建小组'); window.location.href = '/login'; }
            else { msg.innerHTML = `<div class="text-danger">${res.body.error || '创建失败'}</div>`; }
        }).catch(err=>{ console.error('创建小组失败', err); msg.innerHTML = '<div class="text-danger">创建失败，请稍后重试</div>'; });
}

function escapeHtml(s){ if(!s) return ''; return s.replace(/[&<>"']/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]; }); }

// 高级搜索和筛选功能
function applyAdvancedFilters() {
    const keyword = document.getElementById('searchInput').value.trim();
    const location = document.getElementById('locationFilter').value.trim();
    const dateFrom = document.getElementById('dateFromFilter').value;
    const dateTo = document.getElementById('dateToFilter').value;
    const tags = document.getElementById('tagsFilter').value.trim();
    const sortBy = document.getElementById('sortFilter').value;

    // 构建查询参数
    const params = new URLSearchParams();
    params.append('type', currentSearchType);
    
    if (keyword) params.append('keyword', keyword);
    if (location) params.append('location', location);
    if (dateFrom) params.append('date_from', dateFrom);
    if (dateTo) params.append('date_to', dateTo);
    if (tags) params.append('tags', tags);
    if (sortBy) params.append('sort_by', sortBy);

    // 显示搜索中状态
    const container = document.getElementById('activity-list');
    container.innerHTML = `
        <div class="col-12 text-center">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">搜索中...</span>
            </div>
            <p class="mt-3">正在搜索中...</p>
        </div>
    `;

    // 调用搜索API
    fetch(`/api/activities/search?${params.toString()}`)
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
                                <i class="fas fa-search"></i> 没有找到符合条件的活动
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
                                    <i class="fas fa-check-circle"></i> 找到 ${data.count} 个活动
                                </span>
                                <button class="btn btn-sm btn-outline-secondary" onclick="clearFilters()">
                                    清除筛选
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
                            <i class="fas fa-exclamation-circle"></i> 搜索失败：${data.error || '未知错误'}
                        </div>
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('搜索失败:', error);
            container.innerHTML = `
                <div class="col-12">
                    <div class="alert alert-danger">
                        <i class="fas fa-exclamation-circle"></i> 搜索失败，请稍后重试
                    </div>
                </div>
            `;
        });
}

function clearFilters() {
    document.getElementById('searchInput').value = '';
    document.getElementById('locationFilter').value = '';
    document.getElementById('dateFromFilter').value = '';
    document.getElementById('dateToFilter').value = '';
    document.getElementById('tagsFilter').value = '';
    document.getElementById('sortFilter').value = 'newest';
    currentSearchType = 'all';
    
    // 重置类型按钮状态
    document.querySelectorAll('#activityTypeButtons .btn').forEach(btn => {
        btn.classList.remove('active', 'btn-primary');
        btn.classList.add('btn-outline-primary');
    });
    document.querySelector('#activityTypeButtons .btn:first-child').classList.add('active', 'btn-primary');
    document.querySelector('#activityTypeButtons .btn:first-child').classList.remove('btn-outline-primary');
    
    loadActivities();
}