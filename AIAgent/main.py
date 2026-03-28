import webview
import threading
import schedule
import time
import os
import ctypes
import pystray
from PIL import Image, ImageDraw
import datetime

import database as db
import blocker
import ai_chat
import requests

BASE_URL = "https://neuralis-ai-tutor.onrender.com"

class Api:
    def __init__(self):
        self.window = None
        self.current_user_id = None
        self.auth_token = None

    def set_window(self, window):
        self.window = window

    def register(self, username, password, role="student"):
        try:
            r = requests.post(f"{BASE_URL}/register", json={"username": username, "password": password, "role": role})
            if r.status_code == 200:
                return {"success": True, "message": "Đăng ký thành công! Mời bạn đăng nhập."}
            elif r.status_code == 429:
                return {"success": False, "message": "Bạn đang thao tác quá nhanh! Vui lòng đợi 1 phút (Chống Brute Force)."}
            else:
                detail = r.json().get("detail", "Lỗi Server")
                if isinstance(detail, list): # Pydantic validation error
                    detail = ", ".join([f"{d['loc'][-1]}: {d['msg']}" for d in detail])
                return {"success": False, "message": f"Lỗi bảo mật: {detail}"}
        except Exception as e:
            return {"success": False, "message": "Không thể kết nối đến Máy Chủ bảo mật."}

    def login(self, username, password, role="student"):
        try:
            r = requests.post(f"{BASE_URL}/login", json={"username": username, "password": password, "role": role})
            if r.status_code == 200:
                data = r.json()
                user_data = data["user_data"]
                self.auth_token = data["access_token"]
                db_id = user_data["id"]
                self.current_user_id = db_id
                
                # Caching local DB info
                try:
                    conn = db.get_db_conn()
                    cursor = conn.cursor()
                    cursor.execute("INSERT OR IGNORE INTO users (id, username, password_hash) VALUES (?, ?, ?)", 
                                (db_id, username, "cloud_user_no_local_hash"))
                    conn.commit()
                    conn.close()
                except Exception as ex:
                    print(f"Lỗi caching DB: {ex}")
                
                # Update local config
                db.set_config_val(db_id, 'profile_full_name', user_data.get('full_name', ''))
                db.set_config_val(db_id, 'profile_parent_link_code', user_data.get('parent_link_code', ''))
                db.set_config_val(db_id, 'linked_student_id', user_data.get('linked_student_id', ''))
                
                reload_schedules()
                return {"success": True, "message": "Đăng nhập thành công", "user_data": user_data}
            elif r.status_code == 429:
                return {"success": False, "message": "Thử mật khẩu quá nhiều lần! Vui lòng đợi 1 phút."}
            else:
                return {"success": False, "message": r.json().get("detail", "Sai thông tin hoặc tài khoản bị khóa.")}
        except Exception as e:
            print(f"Login Error: {e}")
            return {"success": False, "message": f"Chi tiết lỗi nội bộ: {str(e)}"}

    def logout(self):
        self.current_user_id = None
        self.auth_token = None
        import schedule
        schedule.clear('alarm')
        return True

    def _get_headers(self):
        headers = {"Content-Type": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers

    def get_config(self):
        if not self.current_user_id: return None
        return db.get_config(self.current_user_id)
        
    def add_blocked_website(self, site):
        if not self.current_user_id: return False
        config = self.get_config()
        config['websites'].append(site)
        db.set_config_val(self.current_user_id, 'blocked_websites', config['websites'], is_json=True)
        return True

    def remove_blocked_website(self, site):
        if not self.current_user_id: return False
        config = self.get_config()
        try:
            config['websites'].remove(site)
            db.set_config_val(self.current_user_id, 'blocked_websites', config['websites'], is_json=True)
        except ValueError:
            pass
        return True

    def add_blocked_app(self, app):
        if not self.current_user_id: return False
        config = self.get_config()
        config['apps'].append(app)
        db.set_config_val(self.current_user_id, 'blocked_apps', config['apps'], is_json=True)
        return True

    def remove_blocked_app(self, app):
        if not self.current_user_id: return False
        config = self.get_config()
        try:
            config['apps'].remove(app)
            db.set_config_val(self.current_user_id, 'blocked_apps', config['apps'], is_json=True)
        except ValueError:
            pass
        return True

    def save_api_key(self, api_key):
        return True

    def save_ai_config(self, provider, gemini_key, openai_key, xai_key):
        if not self.current_user_id: return False
        db.set_config_val(self.current_user_id, 'ai_provider', provider)
        db.set_config_val(self.current_user_id, 'api_key', gemini_key)
        db.set_config_val(self.current_user_id, 'openai_api_key', openai_key)
        db.set_config_val(self.current_user_id, 'xai_api_key', xai_key)
        return True

    def get_schedules(self):
        if not self.current_user_id: return []
        # Try fetching from Cloud first
        try:
            r = requests.get(f"{BASE_URL}/schedules/me", headers=self._get_headers(), timeout=5)
            if r.status_code == 200:
                cloud_data = r.json()
                # Update local cache
                for s in cloud_data:
                    db.add_schedule(self.current_user_id, s['task'], s['time'], s['duration'], s['strict_mode'])
                return cloud_data
        except:
            pass
        return db.get_schedules(self.current_user_id)

    def add_schedule(self, task, time, duration, strict_mode=True):
        if not self.current_user_id: return False
        # Add to local first
        db.add_schedule(self.current_user_id, task, time, duration, strict_mode)
        # Sync to Cloud
        try:
            requests.post(f"{BASE_URL}/schedules/me", headers=self._get_headers(),
                          json={"task": task, "time": time, "duration": duration, "strict_mode": strict_mode})
        except: pass
        
        reload_schedules()
        return True

    def delete_schedule(self, schedule_id):
        if not self.current_user_id: return False
        db.remove_schedule(schedule_id, self.current_user_id)
        # Sync to Cloud
        try:
            requests.delete(f"{BASE_URL}/schedules/{schedule_id}", headers=self._get_headers())
        except: pass
        
        reload_schedules()
        return True

    def delete_schedule_by_name(self, task_name):
        # Helper for AI to delete by text name
        schedules = self.get_schedules()
        for s in schedules:
            if task_name.lower() in s['task'].lower():
                return self.delete_schedule(s['id'])
        return {"success": False, "message": "Không tìm thấy nhiệm vụ trùng khớp."}

    # --- Remote Management for Parents ---
    def get_remote_user_profile(self, child_id):
        try:
            r = requests.get(f"{BASE_URL}/user/{child_id}")
            return r.json() if r.status_code == 200 else None
        except: return None

    def get_remote_schedules(self, child_id):
        try:
            r = requests.get(f"{BASE_URL}/schedules/{child_id}")
            return r.json() if r.status_code == 200 else []
        except: return []

    def add_remote_schedule(self, child_id, task, time, duration):
        try:
            # Note: Parent adds via special endpoint or we use their current child context
            r = requests.post(f"{BASE_URL}/schedules/me", headers=self._get_headers(),
                               json={"task": task, "time": time, "duration": duration, "strict_mode": True})
            return {"success": r.status_code == 200}
        except: return {"success": False}

    def delete_remote_schedule(self, child_id, schedule_id):
        try:
            r = requests.delete(f"{BASE_URL}/schedules/{schedule_id}", headers=self._get_headers())
            return {"success": r.status_code == 200}
        except: return {"success": False}

    def link_parent_student(self, code):
        if not self.current_user_id: return {"success": False}
        try:
            r = requests.post(f"{BASE_URL}/link", headers=self._get_headers(), json={"parent_link_code": code})
            return r.json()
        except: return {"success": False, "message": "Lỗi kết nối Server"}


    # --- Chat APIs ---
    def get_chat_sessions(self):
        if not self.current_user_id: return []
        return db.get_chat_sessions(self.current_user_id)

    def get_chat_history(self, session_id):
        return db.get_chat_history(session_id)

    def create_chat_session(self, title):
        if not self.current_user_id: return -1
        return db.create_chat_session(self.current_user_id, title)
        
    def delete_chat_session(self, session_id):
        if not self.current_user_id: return False
        db.delete_chat_session(session_id, self.current_user_id)
        return True

    def get_dashboard_data(self):
        if not self.current_user_id: return None
        today = datetime.datetime.now().date()
        date_list = [(today - datetime.timedelta(days=i)).strftime('%Y-%m-%d') for i in range(6, -1, -1)]
        start_date = date_list[0]
        end_date = date_list[-1]
        
        logs = db.get_dashboard_logs(self.current_user_id, start_date, end_date)
        logs_by_date = {log['date']: log for log in logs}
        
        weekly_focus = []
        total_focus_seconds_today = 0
        blocked_summary_today = {}
        
        for d in date_list:
            if d in logs_by_date:
                sec = logs_by_date[d]['focus']
                weekly_focus.append(sec)
                if d == end_date:
                    total_focus_seconds_today = sec
                    blocked_summary_today = logs_by_date[d]['blocks']
            else:
                weekly_focus.append(0)

        prev_today = date_list[-2] if len(date_list) > 1 else None
        prev_focus_seconds = logs_by_date[prev_today]['focus'] if prev_today and prev_today in logs_by_date else 0
        trend_percent = 0
        if prev_focus_seconds > 0:
            trend_percent = round((total_focus_seconds_today - prev_focus_seconds) / prev_focus_seconds * 100)
            
        weekly_labels = [(today - datetime.timedelta(days=i)).strftime('%a') for i in range(6, -1, -1)]
            
        return {
            'today_focus_seconds': total_focus_seconds_today,
            'trend_percent': trend_percent,
            'weekly_focus': weekly_focus,
            'blocked_summary_today': blocked_summary_today,
            'weekly_labels': weekly_labels
        }

    def save_parent_pin(self, pin):
        if not self.current_user_id: return False
        db.set_config_val(self.current_user_id, 'parent_pin', pin)
        return True

    def verify_parent_pin(self, pin):
        if not self.current_user_id: return False
        saved_pin = db.get_config_val(self.current_user_id, 'parent_pin', '')
        return str(saved_pin) == str(pin)

    def has_parent_pin(self):
        if not self.current_user_id: return False
        return bool(db.get_config_val(self.current_user_id, 'parent_pin', ''))

    def clear_parent_pin(self):
        if not self.current_user_id: return False
        db.set_config_val(self.current_user_id, 'parent_pin', '')
        return True

    def get_ai_insights(self):
        if not self.current_user_id: return "Đang tải dữ liệu..."
        dash_data = self.get_dashboard_data()
        if not dash_data or dash_data.get('today_focus_seconds', 0) == 0:
            return "Hôm nay học sinh chưa bắt đầu phiên học nào. Hãy khuyến khích con học nhé!"
            
        import ai_chat
        config = self.get_config()
        ai_provider = config.get('ai_provider', 'gemini')
        api_key = config.get('api_key', '')
        if ai_provider == 'openai':
            api_key = config.get('openai_api_key', '')
        elif ai_provider == 'xai':
            api_key = config.get('xai_api_key', '')

        if not api_key: 
            return "Vui lòng cấu hình API Key trong mục Cài đặt để AI có thể đưa ra lời khuyên."
        
        prompt = f"Phân tích dữ liệu học tập hôm nay và viết 1 câu Insights (dưới 40 từ) cho Phụ huynh:\n" \
                 f"- Thời gian học: {dash_data['today_focus_seconds'] // 60} phút (Tăng/giảm: {dash_data['trend_percent']}% so với hôm qua)\n" \
                 f"- Lần vi phạm (chơi game/lướt web): {dash_data['blocked_summary_today']}\n" \
                 f"Nếu tốt hãy khen, nếu vi phạm nhiều hãy khuyên nhắc nhở."
                 
        return ai_chat.generate_chat_response(ai_provider, api_key, prompt, [], {})

    def chat_with_ai(self, session_id, user_msg):
        if not self.current_user_id: return "Vui lòng đăng nhập trước"
        config = self.get_config()
        schedules = self.get_schedules()
        
        # Real-time Context payload
        global is_active_block, focus_timer, current_focus_task, current_focus_duration, current_focus_start
        active_focus = None
        if is_active_block:
            time_passed = (time.time() - current_focus_start) / 60
            time_left = max(0, int(current_focus_duration - time_passed))
            active_focus = {
                'task': current_focus_task,
                'time_left_mins': time_left
            }

        # 1. Fetch History
        history = db.get_chat_history(session_id)
        
        # 2. Add user message to DB
        db.save_chat_message(session_id, 'user', user_msg)
        
        # 3. Call AI
        ai_reply = ai_chat.generate_chat_response(config, user_msg, schedules, history, active_focus)
        
        # 4. Add AI reply to DB
        db.save_chat_message(session_id, 'ai', ai_reply)
        return ai_reply

    def rename_chat_session(self, session_id, new_title):
        if not self.current_user_id: return False
        try:
            conn = db.get_db_connection()
            cur = conn.cursor()
            cur.execute("UPDATE chat_sessions SET title = ? WHERE id = ? AND user_id = ?", (new_title, session_id, self.current_user_id))
            conn.commit()
            conn.close()
            return True
        except:
            return False

    def sync_to_server(self):
        if not self.auth_token: return False
        config = self.get_config()
        xp = int(config.get('xp', 0))
        level = (xp // 100) + 1
        badges_count = len(config.get('unlocked_badges', []))
        try:
            requests.post(f"{BASE_URL}/sync", headers=self._get_headers(), json={
                "total_xp": xp,
                "level": level,
                "badges_count": badges_count
            })
        except:
            pass

    def get_leaderboard(self):
        try:
            r = requests.get(f"{BASE_URL}/leaderboard")
            if r.status_code == 200:
                return r.json()
        except:
            pass
        return []

    def link_parent_account(self, code):
        if not self.auth_token: return {"success": False, "message": "No account"}
        try:
            r = requests.post(f"{BASE_URL}/link", headers=self._get_headers(), json={
                "parent_link_code": code
            })
            if r.status_code == 200:
                db.set_config_val(self.current_user_id, 'linked_student_code', code)
                return r.json()
            return {"success": False, "message": r.json().get('detail', 'Lỗi liên kết')}
        except:
            return {"success": False, "message": "Không thể kết nối đến Máy Chủ"}

    def get_user_profile(self):
        if not self.current_user_id: return None
        config = self.get_config()
        
        # Profile Info
        joined_date = config.get('joined_date', '')
        today = datetime.datetime.now().date()
        if not joined_date:
            joined_date = today.strftime('%d/%m/%Y')
            db.set_config_val(self.current_user_id, 'joined_date', joined_date)
            
        full_name = config.get('full_name', '')
        email = config.get('email', '')
        address = config.get('address', '')
        father_name = config.get('father_name', '')
        mother_name = config.get('mother_name', '')
        parent_code = config.get('parent_code', '')
        
        # Gamification vars
        xp = int(config.get('xp', 0))
        streak = int(config.get('streak', 0))
        last_check_in = config.get('last_check_in', '')
        
        # Check if missed a day -> reset streak
        if last_check_in:
            last_date = datetime.datetime.strptime(last_check_in, '%Y-%m-%d').date()
            if (today - last_date).days > 1 and streak > 0:
                streak = 0
                db.set_config_val(self.current_user_id, 'streak', 0)
                
                # Auto generate AI warning msg
                session_id = db.create_chat_session(self.current_user_id, "Thông báo: Mất chuỗi học tập")
                ai_msg = "Bạn đã quên học bài vào ngày hôm qua. Hãy cố gắng chăm chỉ hơn để tiếp tục nhận phần thưởng nhé!"
                db.save_chat_message(session_id, 'ai', ai_msg)
                
        # Level calculation
        level = (xp // 100) + 1
        prev_level_xp = (level - 1) * 100
        next_level_xp = level * 100
        
        rank_name = "Tân Binh"
        if level >= 5: rank_name = "Người Trưởng Thành"
        if level >= 10: rank_name = "Chuyên Gia Tập Trung"
        if level >= 20: rank_name = "Kẻ Hủy Diệt Xao Nhãng"
        
        checked_in_today = (last_check_in == today.strftime('%Y-%m-%d'))
        
        # Badges array
        unlocked_badges = config.get('unlocked_badges', [])
        new_unlocks = False
        
        if streak >= 14 and "streak_14" not in unlocked_badges:
            unlocked_badges.append("streak_14")
            new_unlocks = True
        if streak > 0 and "early_bird" not in unlocked_badges:
            # Mock early_bird unlock logic if streak > 0
            unlocked_badges.append("early_bird")
            new_unlocks = True
            
        if new_unlocks:
            db.set_config_val(self.current_user_id, 'unlocked_badges', unlocked_badges, is_json=True)
            
        total_badges = len(unlocked_badges)
        
        return {
            "joined_date": joined_date,
            "full_name": full_name,
            "email": email,
            "address": address,
            "father_name": father_name,
            "mother_name": mother_name,
            "parent_code": config.get('profile_parent_link_code', parent_code), # Lấy từ Server
            "xp": xp,
            "level": level,
            "next_level_xp": next_level_xp,
            "prev_level_xp": prev_level_xp,
            "rank_name": rank_name,
            "streak": streak,
            "checked_in_today": checked_in_today,
            "unlocked_badges": unlocked_badges,
            "total_badges": total_badges
        }

    def update_user_profile(self, data):
        if not self.current_user_id: return {"success": False, "message": "No account"}
        try:
            for key in ['full_name', 'email', 'address', 'father_name', 'mother_name', 'parent_code']:
                if key in data:
                    db.set_config_val(self.current_user_id, key, data[key])
            return {"success": True, "message": "Thông tin cá nhân đã được cập nhật thành công!"}
        except Exception as e:
            print("Error updating profile:", e)
            return {"success": False, "message": "Có lỗi khi lưu thông tin."}

    def daily_check_in(self):
        if not self.current_user_id: return {"success": False, "message": "Chưa đăng nhập"}
        config = self.get_config()
        
        today = datetime.datetime.now().date()
        today_str = today.strftime('%Y-%m-%d')
        last_check_in = config.get('last_check_in', '')
        
        if last_check_in == today_str:
            return {"success": False, "message": "Hôm nay bạn đã điểm danh rồi!"}
            
        xp = int(config.get('xp', 0))
        streak = int(config.get('streak', 0))
        
        # If consecutive
        if last_check_in:
            last_date = datetime.datetime.strptime(last_check_in, '%Y-%m-%d').date()
            if (today - last_date).days == 1:
                streak += 1
            elif (today - last_date).days > 1:
                streak = 1 # Start new streak
        else:
            streak = 1

        # Check weekday -> 0:Mon, ..., 5:Sat, 6:Sun
        if today.weekday() >= 5:
            gained_xp = 50
        else:
            gained_xp = 20
            
        xp += gained_xp
        
        db.set_config_val(self.current_user_id, 'xp', xp)
        db.set_config_val(self.current_user_id, 'streak', streak)
        db.set_config_val(self.current_user_id, 'last_check_in', today_str)
        
        self.sync_to_server()
        
        return {"success": True, "gained_xp": gained_xp, "streak": streak, "total_xp": xp}
        
    def stop_focus_mode(self):
        global is_active_block, focus_timer
        if is_active_block:
            is_active_block = False
            blocker.unblock_websites()
            if focus_timer:
                focus_timer.cancel()
            print("Đã dừng chế độ tập trung khẩn cấp.")
        return True

# --- Background Scheduler Logic ---
is_active_block = False
focus_timer = None
current_focus_task = ""
current_focus_duration = 0
current_focus_start = 0

def create_tray_icon():
    # Make a simple 64x64 B&W icon using Pillow
    img = Image.new('RGB', (64, 64), color=(0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([16, 16, 48, 48], fill=(255, 255, 255))
    return img

def get_foreground_window_title():
    try:
        hWnd = ctypes.windll.user32.GetForegroundWindow()
        length = ctypes.windll.user32.GetWindowTextLengthW(hWnd)
        buf = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.GetWindowTextW(hWnd, buf, length + 1)
        return buf.value
    except:
        return ""

def close_active_tab():
    try:
        VK_CONTROL = 0x11
        VK_W = 0x57
        ctypes.windll.user32.keybd_event(VK_CONTROL, 0, 0, 0)
        ctypes.windll.user32.keybd_event(VK_W, 0, 0, 0)
        ctypes.windll.user32.keybd_event(VK_W, 0, 2, 0)
        ctypes.windll.user32.keybd_event(VK_CONTROL, 0, 2, 0)
    except:
        pass

def create_tray():
    def on_show(icon, item):
        api.window.show()
    
    def on_exit(icon, item):
        icon.stop()
        api.window.destroy()
        os._exit(0)

    menu = pystray.Menu(
        pystray.MenuItem('Open Agent', on_show, default=True),
        pystray.MenuItem('Exit', on_exit)
    )
    
    icon = pystray.Icon("AIAgent", create_tray_icon(), "AI Agent Menu", menu)
    icon.run()

def reload_schedules():
    schedule.clear('alarm')
    if not api.current_user_id: return
    for s in db.get_schedules(api.current_user_id):
        def alarm_job(task=s['task'], dur=s['duration'], strict=s['strict_mode']):
            trigger_alarm(task, dur, strict)
            
        schedule.every().day.at(s['time']).do(alarm_job).tag('alarm')
        print(f"Scheduled alarm for {s['time']} - {s['task']} (Strict: {s['strict_mode']})")

def trigger_alarm(task, duration_mins, strict_mode):
    global is_active_block, focus_timer
    print(f"Báo thức học tập! {task}")
    api.window.show()
    # Execute JS to show alarm overlay
    api.window.evaluate_js(f'window.showAlarm("{task}");')
    
    if strict_mode:
        # Enable App Blocking Loop inside a thread
        is_active_block = True
        global current_focus_task, current_focus_duration, current_focus_start
        current_focus_task = task
        current_focus_duration = duration_mins
        current_focus_start = time.time()
        
        config = db.get_config(api.current_user_id) or {}
        
        # Attempt to block websites
        blocker.block_websites(config['websites'])
        
        # In 'duration_mins', turn off the block
        def stop_block():
            global is_active_block
            if is_active_block:
                is_active_block = False
                blocker.unblock_websites()
                print(f"Đã kết thúc chế độ chặn cho: {task}")
                # Tell JS focus is over
                try: api.window.evaluate_js('window.endFocusMode();')
                except: pass
            
        focus_timer = threading.Timer(duration_mins * 60, stop_block)
        focus_timer.start()
        # Tell JS that focus started strictly
        api.window.evaluate_js('window.startFocusMode();')
    else:
        print(f"Chế độ học tập bình thường (Không khóa ứng dụng) cho: {task}")

def block_loop():
    global is_active_block
    last_warn_time = 0
    last_warned_site = ""

    while True:
        if is_active_block and api.window and api.current_user_id:
            today_str = datetime.datetime.now().strftime('%Y-%m-%d')
            # 1. Log focus time
            db.log_activity_focus_time(api.current_user_id, today_str, 2)
            
            config = db.get_config(api.current_user_id) or {}
            
            # 2. Prevent blocked apps
            killed_apps = blocker.scan_and_kill_apps(config.get('apps', []))
            if killed_apps:
                for app_name in killed_apps:
                    db.log_activity_blocked_attempt(api.current_user_id, today_str, f"App: {app_name}")
                    
                now = time.time()
                if now - last_warn_time > 5:
                    msg = "Apps: " + ", ".join(killed_apps)
                    try:
                        api.window.evaluate_js(f'window.showBlockWarning("{msg}");')
                        last_warn_time = now
                    except:
                        pass
                        
            # 3. Prevent blocked websites via window title
            active_title = get_foreground_window_title().lower()
            if "ai study agent" not in active_title:
                for site in config.get('websites', []):
                    site_name = site.split('.')[0].lower()
                    if len(site_name) > 2 and site_name in active_title:
                        # Aggressive Tab/Window Closure
                        close_active_tab()
                        db.log_activity_blocked_attempt(api.current_user_id, today_str, f"Web: {site_name}")
                        
                        now = time.time()
                        if site_name != last_warned_site or (now - last_warn_time > 5):
                            try:
                                api.window.evaluate_js(f'window.showBlockWarning("Trang web: {site}");')
                                last_warned_site = site_name
                                last_warn_time = now
                            except Exception:
                                pass
                        break
        time.sleep(2)

def run_scheduler():
    reload_schedules()
    while True:
        schedule.run_pending()
        time.sleep(1)

api = Api()

if __name__ == '__main__':
    html_path = os.path.join(os.path.dirname(__file__), 'web', 'index.html')
    
    # Create webview window
    window = webview.create_window(
        title='AI Study Agent', 
        url=f'file://{html_path}',
        js_api=api,
        width=900, height=650,
        frameless=False,  # Set True for custom drag
        background_color='#0c0c0c',
        # To make it appear above everything when alarm triggers, we use top-most feature.
    )
    api.set_window(window)

    # Start threads
    threading.Thread(target=run_scheduler, daemon=True).start()
    threading.Thread(target=block_loop, daemon=True).start()
    threading.Thread(target=create_tray, daemon=True).start()

    # Start app (this blocks until exited)
    webview.start(debug=False)
