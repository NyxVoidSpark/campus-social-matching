// 页面加载完成后立即加载活动数据
document.addEventListener('DOMContentLoaded', function() {
    loadActivities();
});

// 加载所有活动数据（调用后端API）
function loadActivities() {
    fetch('/api/activities')
        .then(response => {
            if (!response.ok) {
                throw new Error('网络请求失败');
            }
            return response.json();
        })
        .then(activities => {
            displayActivities(activities);
        })
        .catch(error => {
            console.error('获取活动数据失败:', error);
            const container = document.getElementById('activity-list');
            container.innerHTML = `
                <div class="col-12">
                    <div class="alert alert-danger text-center" role="alert">
                        ? 加载失败，请刷新页面重试
                    </div>
                </div>
            `;
        });
}

// 渲染活动列表到页面
function displayActivities(activities) {
    const container = document.getElementById('activity-list');
    container.innerHTML = ''; // 清空加载状态

    // 若没有活动数据，显示提示
    if (activities.length === 0) {
        container.innerHTML = `
            <div class="col-12">
                <div class="alert alert-warning text-center" role="alert">
                    ?? 暂无活动数据，敬请期待
                </div>
            </div>
        `;
        return;
    }

    // 循环渲染每个活动卡片
    activities.forEach(activity => {
        const activityCard = `
            <div class="col-md-4 mb-4">
                <div class="card h-100">
                    <div class="card-body">
                        <h5 class="card-title">${activity.title}</h5>
                        <p class="card-text">
                            <span class="badge bg-primary">${activity.type}</span><br>
                            <small class="text-muted">
                                ? ${activity.time}<br>
                                ? ${activity.location}
                            </small>
                        </p>
                        <button class="btn btn-sm btn-outline-primary w-100" onclick="joinActivity(${activity.id})">
                            我要参加
                        </button>
                    </div>
                </div>
            </div>
        `;
        container.innerHTML += activityCard;
    });
}

// 报名参加活动（调用后端报名API）
function joinActivity(activityId) {
    fetch(`/api/activities/${activityId}/join`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('报名请求失败');
        }
        return response.json();
    })
    .then(data => {
        alert(data.message); // 显示报名成功提示
    })
    .catch(error => {
        console.error('报名失败:', error);
        alert('? 报名失败，请重试');
    });
}