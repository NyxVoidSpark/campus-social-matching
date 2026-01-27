// 现代化首页功能
document.addEventListener('DOMContentLoaded', function() {
    loadStats();
    setupSearch();
    setupFilters();
});

// 加载统计数据
function loadStats() {
    fetch('/api/stats/overview')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('totalActivities').textContent = data.data.activities.total;
                document.getElementById('activeUsers').textContent = data.data.users.new_today;
                document.getElementById('totalPosts').textContent = data.data.posts.total;
            }
        })
        .catch(error => console.error('加载统计失败:', error));
}

// 设置搜索功能
function setupSearch() {
    const searchInput = document.getElementById('searchInput');

    // 添加搜索建议
    searchInput.addEventListener('input', function() {
        const query = this.value.trim();
        if (query.length > 2) {
            showSearchSuggestions(query);
        } else {
            hideSearchSuggestions();
        }
    });

    // 点击外部隐藏建议
    document.addEventListener('click', function(e) {
        if (!searchInput.contains(e.target)) {
            hideSearchSuggestions();
        }
    });
}

// 显示搜索建议
function showSearchSuggestions(query) {
    // 这里可以实现搜索建议功能
    console.log('搜索建议:', query);
}

// 隐藏搜索建议
function hideSearchSuggestions() {
    // 隐藏搜索建议框
}

// 全局搜索
function searchAll() {
    const query = document.getElementById('searchInput').value.trim();
    if (query) {
        // 跳转到搜索结果页面或在当前页面显示结果
        window.location.href = `/search?q=${encodeURIComponent(query)}`;
    }
}

// 按类别筛选
function filterByCategory(category) {
    // 更新URL参数并重新加载内容
    const url = new URL(window.location);
    url.searchParams.set('category', category);
    window.location.href = url.toString();
}

// 显示附近活动
function showNearby() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function(position) {
            const lat = position.coords.latitude;
            const lng = position.coords.longitude;

            // 使用地理位置过滤活动
            const url = new URL(window.location);
            url.searchParams.set('lat', lat);
            url.searchParams.set('lng', lng);
            url.searchParams.set('nearby', 'true');
            window.location.href = url.toString();
        }, function(error) {
            alert('无法获取您的位置信息，请允许浏览器访问位置权限。');
        });
    } else {
        alert('您的浏览器不支持地理位置功能。');
    }
}

// 设置筛选器
function setupFilters() {
    // 添加更多筛选功能
    const filterButtons = document.querySelectorAll('.badge[cursor-pointer]');

    filterButtons.forEach(button => {
        button.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.05)';
        });

        button.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
        });
    });
}

// 加载用户信息
function loadUserInfo() {
    fetch('/api/current-user')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('usernameDisplay').textContent = data.data.username;

                // 显示用户角色
                const roleBadge = document.getElementById('userRoleBadge');
                if (data.data.role === 'teacher') {
                    roleBadge.textContent = '教师';
                    roleBadge.classList.remove('hidden');
                }
            }
        })
        .catch(error => console.error('加载用户信息失败:', error));
}

// 登出功能
function logout() {
    if (confirm('确定要退出登录吗？')) {
        fetch('/api/logout', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    window.location.href = '/login';
                }
            })
            .catch(error => console.error('登出失败:', error));
    }
}

// 页面滚动效果
window.addEventListener('scroll', function() {
    const navbar = document.querySelector('.navbar');
    if (window.scrollY > 100) {
        navbar.classList.add('shadow-lg');
    } else {
        navbar.classList.remove('shadow-lg');
    }
});

// 动画效果
function animateOnScroll() {
    const elements = document.querySelectorAll('.animate-on-scroll');

    elements.forEach(element => {
        const elementTop = element.getBoundingClientRect().top;
        const elementBottom = element.getBoundingClientRect().bottom;

        if (elementTop < window.innerHeight && elementBottom > 0) {
            element.classList.add('animate-fade-in');
        }
    });
}

window.addEventListener('scroll', animateOnScroll);
window.addEventListener('load', animateOnScroll);