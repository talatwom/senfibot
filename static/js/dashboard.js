// اسکریپت‌های داشبورد مدیریتی

// نمودارها
let dailyReportsChart;
let eventDistributionChart;

// تابع بروزرسانی وضعیت سرور
function updateServerStatus() {
    fetch('/api/server_status')
        .then(response => response.json())
        .then(data => {
            // بروزرسانی نشانگر وضعیت
            const statusIndicator = document.getElementById('server-status-indicator');
            const statusText = document.getElementById('server-status-text');
            
            if (data.is_running) {
                statusIndicator.className = 'status-indicator status-online';
                statusText.textContent = 'سرور فعال است';
            } else {
                statusIndicator.className = 'status-indicator status-offline';
                statusText.textContent = 'سرور غیرفعال است';
            }
            
            // بروزرسانی آپ‌تایم
            document.getElementById('uptime').textContent = data.uptime_formatted;
            
            // بروزرسانی CPU و حافظه
            document.getElementById('cpu-usage').textContent = data.cpu_percent + '%';
            document.getElementById('memory-usage').textContent = data.memory_percent + '%';
        })
        .catch(error => {
            console.error('Error fetching server status:', error);
            const statusIndicator = document.getElementById('server-status-indicator');
            const statusText = document.getElementById('server-status-text');
            statusIndicator.className = 'status-indicator status-offline';
            statusText.textContent = 'خطا در ارتباط با سرور';
        });
}

// تابع بروزرسانی آمار کاربران
function updateUserStats() {
    fetch('/api/user_stats')
        .then(response => response.json())
        .then(data => {
            document.getElementById('total-users').textContent = data.total_users;
            document.getElementById('active-users').textContent = data.active_users;
            document.getElementById('admin-users').textContent = data.admin_users;
        })
        .catch(error => console.error('Error fetching user stats:', error));
}

// تابع بروزرسانی آمار گزارش‌ها
function updateReportStats() {
    fetch('/api/report_stats')
        .then(response => response.json())
        .then(data => {
            document.getElementById('total-reports').textContent = data.total_reports;
            
            // محاسبه میانگین روزانه
            const dailySum = data.daily_stats.reduce((sum, day) => sum + day.count, 0);
            const avgDaily = (dailySum / data.daily_stats.length).toFixed(1);
            document.getElementById('avg-daily-reports').textContent = avgDaily;
            
            // بروزرسانی نمودار گزارش‌های روزانه
            updateDailyReportsChart(data.daily_stats);
        })
        .catch(error => console.error('Error fetching report stats:', error));
}

// تابع بروزرسانی آمار رویدادها
function updateLogStats() {
    fetch('/api/log_stats')
        .then(response => response.json())
        .then(data => {
            document.getElementById('total-logs').textContent = data.total_logs;
            
            // یافتن تعداد خطاهای ورود و AI
            const loginFailures = data.event_stats.find(e => e.type === 'login_failed');
            const aiErrors = data.event_stats.find(e => e.type === 'ai_error');
            
            document.getElementById('login-failures').textContent = loginFailures ? loginFailures.count : 0;
            document.getElementById('ai-errors').textContent = aiErrors ? aiErrors.count : 0;
            
            // بروزرسانی نمودار توزیع رویدادها
            updateEventDistributionChart(data.event_stats);
        })
        .catch(error => console.error('Error fetching log stats:', error));
}

// تابع بروزرسانی آخرین رویدادها
function updateRecentLogs() {
    // نمایش نشانگر بارگذاری
    const tableBody = document.getElementById('logs-table-body');
    tableBody.innerHTML = '<tr><td colspan="4" class="text-center"><div class="loading"></div> در حال بارگذاری...</td></tr>';
    
    fetch('/api/recent_logs')
        .then(response => response.json())
        .then(data => {
            tableBody.innerHTML = '';
            
            data.forEach(log => {
                const row = document.createElement('tr');
                
                const dateCell = document.createElement('td');
                dateCell.textContent = log.date;
                row.appendChild(dateCell);
                
                const userIdCell = document.createElement('td');
                userIdCell.textContent = log.user_id;
                row.appendChild(userIdCell);
                
                const eventTypeCell = document.createElement('td');
                // ترجمه نوع رویداد
                let eventType = log.event_type;
                switch(eventType) {
                    case 'start_bot':
                        eventType = 'شروع بات';
                        break;
                    case 'login_success':
                        eventType = 'ورود موفق';
                        break;
                    case 'login_failed':
                        eventType = 'خطای ورود';
                        break;
                    case 'draft_generated':
                        eventType = 'تولید پیش‌نویس';
                        break;
                    case 'report_confirmed':
                        eventType = 'تأیید گزارش';
                        break;
                    case 'ai_error':
                        eventType = 'خطای هوش مصنوعی';
                        break;
                }
                eventTypeCell.textContent = eventType;
                row.appendChild(eventTypeCell);
                
                const detailsCell = document.createElement('td');
                if (typeof log.details === 'object' && log.details !== null) {
                    detailsCell.textContent = JSON.stringify(log.details);
                } else {
                    detailsCell.textContent = log.details || '-';
                }
                row.appendChild(detailsCell);
                
                tableBody.appendChild(row);
            });
            
            if (data.length === 0) {
                const row = document.createElement('tr');
                const cell = document.createElement('td');
                cell.setAttribute('colspan', '4');
                cell.textContent = 'هیچ رویدادی یافت نشد.';
                cell.className = 'text-center';
                row.appendChild(cell);
                tableBody.appendChild(row);
            }
        })
        .catch(error => {
            console.error('Error fetching recent logs:', error);
            const tableBody = document.getElementById('logs-table-body');
            tableBody.innerHTML = `<tr><td colspan="4" class="text-center text-danger">خطا در بارگذاری رویدادها: ${error.message}</td></tr>`;
        });
}

// تابع بروزرسانی نمودار گزارش‌های روزانه
function updateDailyReportsChart(data) {
    const ctx = document.getElementById('daily-reports-chart').getContext('2d');
    
    // ایجاد نمودار جدید در صورت نیاز
    if (!dailyReportsChart) {
        dailyReportsChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.map(day => day.date),
                datasets: [{
                    label: 'تعداد گزارش‌ها',
                    data: data.map(day => day.count),
                    backgroundColor: 'rgba(54, 162, 235, 0.5)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                }
            }
        });
    } else {
        // بروزرسانی داده‌های نمودار موجود
        dailyReportsChart.data.labels = data.map(day => day.date);
        dailyReportsChart.data.datasets[0].data = data.map(day => day.count);
        dailyReportsChart.update();
    }
}

// تابع بروزرسانی نمودار توزیع رویدادها
function updateEventDistributionChart(data) {
    const ctx = document.getElementById('event-distribution-chart').getContext('2d');
    
    // ترجمه انواع رویدادها
    const translatedData = data.map(item => {
        let translatedType = item.type;
        switch(item.type) {
            case 'start_bot':
                translatedType = 'شروع بات';
                break;
            case 'login_success':
                translatedType = 'ورود موفق';
                break;
            case 'login_failed':
                translatedType = 'خطای ورود';
                break;
            case 'draft_generated':
                translatedType = 'تولید پیش‌نویس';
                break;
            case 'report_confirmed':
                translatedType = 'تأیید گزارش';
                break;
            case 'ai_error':
                translatedType = 'خطای هوش مصنوعی';
                break;
        }
        return {
            type: translatedType,
            count: item.count
        };
    });
    
    // تولید رنگ‌های تصادفی
    const backgroundColors = [
        'rgba(255, 99, 132, 0.5)',
        'rgba(54, 162, 235, 0.5)',
        'rgba(255, 206, 86, 0.5)',
        'rgba(75, 192, 192, 0.5)',
        'rgba(153, 102, 255, 0.5)',
        'rgba(255, 159, 64, 0.5)',
        'rgba(199, 199, 199, 0.5)',
        'rgba(83, 102, 255, 0.5)',
        'rgba(40, 159, 64, 0.5)',
        'rgba(210, 199, 199, 0.5)'
    ];
    
    // ایجاد نمودار جدید در صورت نیاز
    if (!eventDistributionChart) {
        eventDistributionChart = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: translatedData.map(item => item.type),
                datasets: [{
                    data: translatedData.map(item => item.count),
                    backgroundColor: backgroundColors.slice(0, translatedData.length),
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                    }
                }
            }
        });
    } else {
        // بروزرسانی داده‌های نمودار موجود
        eventDistributionChart.data.labels = translatedData.map(item => item.type);
        eventDistributionChart.data.datasets[0].data = translatedData.map(item => item.count);
        eventDistributionChart.data.datasets[0].backgroundColor = backgroundColors.slice(0, translatedData.length);
        eventDistributionChart.update();
    }
}

// اجرای تابع‌های بروزرسانی هنگام بارگذاری صفحه
document.addEventListener('DOMContentLoaded', function() {
    // بروزرسانی اولیه همه داده‌ها
    updateServerStatus();
    updateUserStats();
    updateReportStats();
    updateLogStats();
    updateRecentLogs();
    
    // تنظیم بروزرسانی‌های دوره‌ای
    setInterval(updateServerStatus, 30000); // هر 30 ثانیه
    setInterval(updateUserStats, 60000); // هر 1 دقیقه
    setInterval(updateReportStats, 60000); // هر 1 دقیقه
    setInterval(updateLogStats, 60000); // هر 1 دقیقه
    
    // رویداد کلیک دکمه بروزرسانی لاگ‌ها
    document.getElementById('refresh-logs').addEventListener('click', updateRecentLogs);
});