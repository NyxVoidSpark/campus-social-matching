// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    loadActivities();
});

// 加载活动数据
function loadActivities() {
    // 这里先模拟一些数据，后面会改成从后端API获取
    const activities = [
        { id: 1, title: "Java编程竞赛", type: "学术", time: "2025-04-15", location: "计算机学院实验室" },
        { id: 2, title: "校园篮球联赛", type: "体育", time: "2025-04-20", location: "体育馆" },
        { id: 3, title: "摄影技巧分享会", type: "艺术", time: "2025-04-18", location: "艺术楼201" }
    ];
    
    displayActivities(activities);
}

// 显示活动列表
function displayActivities(activities) {
    const container = document.getElementById('activity-list');
    container.innerHTML = ''; // 清空加载动画
    
    activities.forEach(activity => {
        const activityCard = `
            <div class="col-md-4 mb-3">
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title">${activity.title}</h5>
                        <p class="card-text">
                            <span class="badge bg-primary">${activity.type}</span><br>
                            <small class="text-muted">
                                ? ${activity.time}<br>
                                ? ${activity.location}
                            </small>
                        </p >
                        <button class="btn btn-sm btn-outline-primary" onclick="joinActivity(${activity.id})">
                            我要参加
                        </button>
                    </div>
                </div>
            </div>
        `;
        container.innerHTML += activityCard;
    });
}

// 参加活动函数
function joinActivity(activityId) {
    alert(`已报名参加活动 ID: ${activityId}`);
    // 这里后面会改成调用后端API
}