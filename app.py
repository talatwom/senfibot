from flask import Flask, render_template, jsonify
import json
import os
from datetime import datetime, timedelta
import psutil
import threading
import time

app = Flask(__name__)

# مسیر فایل‌های داده
USERS_FILE = "users.json"
LOGS_FILE = "logs.json"
REPORTS_FILE = "reports.json"

# متغیر برای ذخیره وضعیت آپ‌تایم سرور
server_uptime = {"start_time": datetime.now(), "is_running": True}

# تابع برای بررسی دوره‌ای آپ‌تایم سرور
def check_server_status():
    while True:
        server_uptime["is_running"] = True
        server_uptime["uptime_seconds"] = (datetime.now() - server_uptime["start_time"]).total_seconds()
        time.sleep(60)  # بررسی هر یک دقیقه

# شروع ترد بررسی وضعیت سرور
status_thread = threading.Thread(target=check_server_status, daemon=True)
status_thread.start()

# روت صفحه اصلی
@app.route('/')
def index():
    return render_template('index.html')

# API برای دریافت آمار کاربران
@app.route('/api/user_stats')
def user_stats():
    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            users = json.load(f)
        
        total_users = len(users)
        active_users = sum(1 for u in users.values() if u.get("is_authenticated", False))
        admin_users = sum(1 for u in users.values() if u.get("role") == "admin")
        regular_users = total_users - admin_users
        
        return jsonify({
            "total_users": total_users,
            "active_users": active_users,
            "admin_users": admin_users,
            "regular_users": regular_users
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# آخرین ۱۰ لاگ
@app.route('/api/recent_logs')
def recent_logs():
    try:
        # خواندن لاگ‌ها
        try:
            with open(LOGS_FILE, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            logs = []
        
        # مرتب‌سازی بر اساس زمان (نزولی)
        logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        # گرفتن ۱۰ لاگ آخر
        recent = logs[:10]
        
        # فرمت‌دهی داده‌ها
        formatted_logs = []
        for log in recent:
            try:
                timestamp = datetime.fromisoformat(log.get("timestamp", ""))
                formatted_date = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                formatted_date = "نامشخص"
            
            formatted_logs.append({
                "date": formatted_date,
                "user_id": log.get("user_id", "نامشخص"),
                "event_type": log.get("event_type", "نامشخص"),
                "details": log.get("details", "")
            })
        
        return jsonify(formatted_logs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# API برای دریافت آمار گزارش‌ها
@app.route('/api/report_stats')
def report_stats():
    try:
        # خواندن گزارش‌ها
        try:
            with open(REPORTS_FILE, 'r', encoding='utf-8') as f:
                reports = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            reports = []
        
        # آمار کلی
        total_reports = len(reports)
        
        # آمار روزانه در ۷ روز گذشته
        daily_stats = {}
        today = datetime.now().date()
        
        for i in range(7):
            date = today - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            daily_stats[date_str] = 0
        
        for report in reports:
            try:
                report_date = datetime.fromisoformat(report["timestamp"]).date()
                date_str = report_date.strftime("%Y-%m-%d")
                if date_str in daily_stats:
                    daily_stats[date_str] += 1
            except (KeyError, ValueError):
                continue
        
        # تبدیل به لیست برای نمودار
        daily_data = [{"date": date, "count": count} for date, count in daily_stats.items()]
        daily_data.reverse()  # مرتب‌سازی از قدیمی به جدید
        
        return jsonify({
            "total_reports": total_reports,
            "daily_stats": daily_data
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# API برای دریافت آمار لاگ‌ها
@app.route('/api/log_stats')
def log_stats():
    try:
        # خواندن لاگ‌ها
        try:
            with open(LOGS_FILE, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            logs = []
        
        # آمار کلی رویدادها
        total_logs = len(logs)
        
        # دسته‌بندی رویدادها
        event_types = {}
        for log in logs:
            event_type = log.get("event_type", "unknown")
            event_types[event_type] = event_types.get(event_type, 0) + 1
        
        # تبدیل به لیست برای نمودار
        event_data = [{"type": event_type, "count": count} for event_type, count in event_types.items()]
        
        return jsonify({
            "total_logs": total_logs,
            "event_stats": event_data
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# API برای دریافت وضعیت سرور
@app.route('/api/server_status')
def server_status():
    try:
        uptime_seconds = server_uptime["uptime_seconds"]
        
        # تبدیل ثانیه به فرمت خوانا
        days, remainder = divmod(uptime_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        uptime_formatted = f"{int(days)} روز, {int(hours)} ساعت, {int(minutes)} دقیقه"
        
        # دریافت اطلاعات سیستم
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        return jsonify({
            "is_running": server_uptime["is_running"],
            "uptime_seconds": uptime_seconds,
            "uptime_formatted": uptime_formatted,
            "cpu_percent": cpu_percent,
            "memory_percent": memory_percent,
            "start_time": server_uptime["start_time"].isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=8000)