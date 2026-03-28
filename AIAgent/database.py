import sqlite3
import json
import os
import hashlib
import binascii

DB_PATH = os.path.join(os.path.dirname(__file__), 'agent_data_v2.db')

def get_db_conn():
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    try:
        conn.execute('PRAGMA journal_mode=WAL;')
    except sqlite3.OperationalError:
        pass
    return conn

def _hash_password(password):
    salt = "ai_agent_salt_123"
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return binascii.hexlify(dk).decode('utf-8')

def init_db():
    conn = get_db_conn()
    cursor = conn.cursor()
    
    # Bảng Tài Khoản Người Dùng
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password_hash TEXT
        )
    ''')
    
    # Bảng Cấu Hình theo User
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS config (
            user_id INTEGER,
            key TEXT,
            value TEXT,
            PRIMARY KEY (user_id, key),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    
    # Bảng Lịch Học theo User
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            task TEXT,
            time TEXT,
            duration INTEGER,
            strict_mode INTEGER DEFAULT 1,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    # Bảng Chat Sessions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    # Bảng Chat History
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            role TEXT,
            content TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
        )
    ''')
    
    # Bảng Activity Logs (Dành cho Dashboard)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date TEXT,
            focus_time_seconds INTEGER DEFAULT 0,
            blocked_attempts TEXT DEFAULT '{}',
            FOREIGN KEY(user_id) REFERENCES users(id),
            UNIQUE(user_id, date)
        )
    ''')
    
    conn.commit()
    conn.close()

# --- Auth functions ---
def register_user(username, password):
    if not username or not password: return False, "Vui lòng nhập đủ thông tin."
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
    if cursor.fetchone():
        conn.close()
        return False, "Tài khoản đã tồn tại!"
        
    pwd_hash = _hash_password(password)
    try:
        cursor.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, pwd_hash))
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Tài khoản đã tồn tại!"
        
    user_id = cursor.lastrowid
    
    # Set default config for new user
    defaults = [
        (user_id, 'ai_provider', 'gemini'),
        (user_id, 'api_key', ''),
        (user_id, 'openai_api_key', ''),
        (user_id, 'xai_api_key', ''),
        (user_id, 'blocked_websites', json.dumps(['youtube.com', 'facebook.com', 'tiktok.com'])),
        (user_id, 'blocked_apps', json.dumps(['steam.exe', 'LeagueClient.exe']))
    ]
    cursor.executemany('INSERT INTO config (user_id, key, value) VALUES (?, ?, ?)', defaults)
    
    conn.commit()
    conn.close()
    return True, "Đăng ký thành công."

def login_user(username, password):
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute('SELECT id, password_hash FROM users WHERE username = ?', (username,))
    row = cursor.fetchone()
    conn.close()
    if row and row[1] == _hash_password(password):
        return True, row[0] # Return user_id
    return False, "Sai tài khoản hoặc mật khẩu."

# --- Config functions ---
def get_config_val(user_id, key, default=None, is_json=False):
    if not user_id: return default
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM config WHERE user_id = ? AND key = ?', (user_id, key))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return json.loads(row[0]) if is_json else row[0]
    return default

def set_config_val(user_id, key, value, is_json=False):
    if not user_id: return
    if is_json:
        value = json.dumps(value)
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute('REPLACE INTO config (user_id, key, value) VALUES (?, ?, ?)', (user_id, key, value))
    conn.commit()
    conn.close()

def get_config(user_id):
    if not user_id: return {}
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute('SELECT key, value FROM config WHERE user_id = ?', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    
    config = {}
    for r in rows:
        key, val = r[0], r[1]
        try:
            if val and (val.startswith('[') or val.startswith('{')):
                config[key] = json.loads(val)
            else:
                config[key] = val
        except:
            config[key] = val
            
    config['ai_provider'] = config.get('ai_provider', 'gemini')
    config['api_key'] = config.get('api_key', '')
    config['openai_api_key'] = config.get('openai_api_key', '')
    config['xai_api_key'] = config.get('xai_api_key', '')
    config['websites'] = config.get('blocked_websites', [])
    config['apps'] = config.get('blocked_apps', [])
    
    return config

# --- Schedule functions ---
def get_schedules(user_id=None):
    # If user_id is None, we can fetch all for the background scheduler, or fetch active user's schedules.
    # We will fetch all schedules for background process, but we need to know what to block.
    # Actually, background process shouldn't block EVERYTHING for ALL users if 1 user scheduled something.
    # Wait, desktop app only has 1 user active at a time? Let's just run schedules for the LOGGED IN user.
    # Below gets schedules for a specific user:
    conn = get_db_conn()
    cursor = conn.cursor()
    if user_id is not None:
        cursor.execute('SELECT id, task, time, duration, strict_mode FROM schedules WHERE user_id = ?', (user_id,))
    else:
        cursor.execute('SELECT id, task, time, duration, strict_mode FROM schedules')
    rows = cursor.fetchall()
    conn.close()
    return [{'id': r[0], 'task': r[1], 'time': r[2], 'duration': r[3], 'strict_mode': bool(r[4])} for r in rows]

def add_schedule(user_id, task, time, duration, strict_mode=True):
    if not user_id: return
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO schedules (user_id, task, time, duration, strict_mode) VALUES (?, ?, ?, ?, ?)', 
                   (user_id, task, time, duration, 1 if strict_mode else 0))
    conn.commit()
    conn.close()

def remove_schedule(schedule_id, user_id=None):
    if not user_id: return
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM schedules WHERE id = ? AND user_id = ?', (schedule_id, user_id))
    conn.commit()
    conn.close()

# --- Chat History Functions ---
def create_chat_session(user_id, title):
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO chat_sessions (user_id, title) VALUES (?, ?)', (user_id, title))
    session_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return session_id

def get_chat_sessions(user_id):
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute('SELECT id, title, created_at FROM chat_sessions WHERE user_id = ? ORDER BY id DESC', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{'id': r[0], 'title': r[1], 'created_at': r[2]} for r in rows]

def get_chat_history(session_id):
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute('SELECT role, content, timestamp FROM chat_history WHERE session_id = ? ORDER BY id ASC', (session_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{'role': r[0], 'content': r[1], 'timestamp': r[2]} for r in rows]

def save_chat_message(session_id, role, content):
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO chat_history (session_id, role, content) VALUES (?, ?, ?)', (session_id, role, content))
    conn.commit()
    conn.close()

def delete_chat_session(session_id, user_id):
    # Due to ON DELETE CASCADE on foreign key, child rows in chat_history are deleted automatically 
    # if PRAGMA foreign_keys is enabled. To be safe, we delete manually first or just use cascade.
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM chat_history WHERE session_id = ?', (session_id,))
    cursor.execute('DELETE FROM chat_sessions WHERE id = ? AND user_id = ?', (session_id, user_id))
    conn.commit()
    conn.close()

def rename_chat_session(session_id, user_id, new_title):
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute('UPDATE chat_sessions SET title = ? WHERE id = ? AND user_id = ?', (new_title, session_id, user_id))
    conn.commit()
    conn.close()

# --- Activity Logging Functions ---
def log_activity_focus_time(user_id, date_str, seconds_added):
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO activity_logs (user_id, date, focus_time_seconds, blocked_attempts)
        VALUES (?, ?, ?, '{}')
        ON CONFLICT(user_id, date) DO UPDATE SET focus_time_seconds = focus_time_seconds + ?
    ''', (user_id, date_str, seconds_added, seconds_added))
    conn.commit()
    conn.close()

def log_activity_blocked_attempt(user_id, date_str, blocked_item):
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute('SELECT blocked_attempts FROM activity_logs WHERE user_id = ? AND date = ?', (user_id, date_str))
    row = cursor.fetchone()
    if row:
        attempts_dict = json.loads(row[0]) if row[0] else {}
        attempts_dict[blocked_item] = attempts_dict.get(blocked_item, 0) + 1
        cursor.execute('UPDATE activity_logs SET blocked_attempts = ? WHERE user_id = ? AND date = ?', 
                      (json.dumps(attempts_dict), user_id, date_str))
    else:
        attempts_dict = {blocked_item: 1}
        cursor.execute('''
            INSERT INTO activity_logs (user_id, date, focus_time_seconds, blocked_attempts)
            VALUES (?, ?, 0, ?)
        ''', (user_id, date_str, json.dumps(attempts_dict)))
    conn.commit()
    conn.close()

def get_dashboard_logs(user_id, start_date, end_date):
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT date, focus_time_seconds, blocked_attempts 
        FROM activity_logs 
        WHERE user_id = ? AND date >= ? AND date <= ?
        ORDER BY date ASC
    ''', (user_id, start_date, end_date))
    rows = cursor.fetchall()
    conn.close()
    return [{'date': r[0], 'focus': r[1], 'blocks': json.loads(r[2])} for r in rows]

init_db()
