from fastapi import FastAPI, HTTPException, Request, Depends, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr, Field
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os
import sqlite3
import random
import string
from typing import Optional, List

from scalar_fastapi import get_scalar_api_reference

# --- RATE LIMITER CONFIG (CHỐNG BRUTE FORCE) ---
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(
    title="Neuralis AI Tutor Ultimate Security Backend",
    description="🚀 Hệ thống bảo mật tối thượng: Brute Force Protection + JWT Pro + SQL Safety.",
    version="3.0.0-ultimate",
    docs_url=None,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- SECURITY CONFIG ---
SECRET_KEY = "NEURALIS_ULTIMATE_SECRET_2026_PRO"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 7 ngày

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- AUTH UTILS ---
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Token vô hiệu")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Phiên làm việc hết hạn")

# --- DATABASE SECURITY layer ---
DB_PATH = os.path.join(os.path.dirname(__file__), "cloud.db")

def query_db(query: str, args=(), one=False):
    # CHỐNG SQL INJECTION: Luôn sử dụng Parameterization
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(query, args)
    rv = cur.fetchall()
    conn.commit()
    conn.close()
    return (rv[0] if rv else None) if one else rv

# --- DATABASE INIT ---
def init_db():
    query_db('''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                role TEXT,
                full_name TEXT,
                parent_link_code TEXT,
                linked_student_id INTEGER,
                total_xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                badges_count INTEGER DEFAULT 0,
                joined_date TEXT)''')
    query_db('''CREATE TABLE IF NOT EXISTS schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                task TEXT,
                time TEXT,
                duration INTEGER,
                strict_mode INTEGER DEFAULT 1,
                FOREIGN KEY(user_id) REFERENCES users(id))''')

init_db()

# --- VALIDATION MODELS (CHỐNG INJECTION & DỮ LIỆU RÁC) ---
class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern="^[a-zA-Z0-9.@%+\\-_]+$")
    password: str = Field(..., min_length=8)
    role: str

class UserLogin(BaseModel):
    username: str = Field(..., min_length=3)
    password: str
    role: str

class SyncData(BaseModel):
    total_xp: int = Field(..., ge=0)
    level: int = Field(..., ge=1)
    badges_count: int = Field(..., ge=0)

class LinkParent(BaseModel):
    parent_link_code: str = Field(..., min_length=5)

class ScheduleItem(BaseModel):
    task: str = Field(..., min_length=2, max_length=100)
    time: str = Field(..., pattern="^[0-9]{2}:[0-9]{2}$")
    duration: int = Field(..., ge=5, le=480)
    strict_mode: bool = True

def generate_link_code():
    return "LINK-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))

# --- ROUTES ---

@app.post("/register", tags=["Authentication"])
@limiter.limit("3/minute") # Chống spam đăng ký
async def register(request: Request, user: UserRegister):
    existing = query_db("SELECT id FROM users WHERE username = ?", (user.username,), one=True)
    if existing:
        raise HTTPException(status_code=400, detail="Username đã tồn tại")
    
    hashed_password = pwd_context.hash(user.password)
    parent_code = generate_link_code() if user.role == "student" else None
    joined_date = datetime.now().strftime("%d/%m/%Y")
    
    query_db('''INSERT INTO users (username, password, role, full_name, parent_link_code, joined_date)
                VALUES (?, ?, ?, ?, ?, ?)''', 
             (user.username, hashed_password, user.role, "Tân binh Neuralis", parent_code, joined_date))
    return {"success": True, "message": "Đăng ký thành công"}

@app.post("/login", tags=["Authentication"])
@limiter.limit("5/minute") # CHỐNG BRUTE FORCE: Thử tối đa 5 lần/phút
async def login(request: Request, user: UserLogin):
    row = query_db("SELECT * FROM users WHERE username = ? AND role = ?", (user.username, user.role), one=True)
    
    if not row or not pwd_context.verify(user.password, row["password"]):
        raise HTTPException(status_code=401, detail="Sai thông tin đăng nhập!")
    
    user_dict = dict(row)
    del user_dict["password"]
    
    token = create_access_token(data={"sub": user_dict["id"]})
    return {
        "success": True,
        "access_token": token,
        "token_type": "bearer",
        "user_data": user_dict
    }

@app.get("/user/me", tags=["User Profiles"])
async def get_me(user_id: int = Depends(get_current_user)):
    row = query_db("SELECT * FROM users WHERE id = ?", (user_id,), one=True)
    if row:
        user_dict = dict(row)
        del user_dict["password"]
        return user_dict
    raise HTTPException(status_code=404)

@app.post("/sync", tags=["User Profiles"])
async def sync_progress(data: SyncData, user_id: int = Depends(get_current_user)):
    current = query_db("SELECT total_xp, level FROM users WHERE id = ?", (user_id,), one=True)
    if not current: raise HTTPException(status_code=404)
    
    # CHỐNG GIẢM CẤP: Chỉ cập nhật nếu giá trị mới LỚN HƠN giá trị hiện tại
    new_xp = max(current["total_xp"], data.total_xp)
    new_level = max(current["level"], data.level)
    
    query_db("UPDATE users SET total_xp = ?, level = ?, badges_count = ? WHERE id = ?", 
             (new_xp, new_level, data.badges_count, user_id))
    return {"success": True, "new_xp": new_xp, "new_level": new_level}

@app.get("/leaderboard", tags=["Gamification"])
async def get_leaderboard():
    rows = query_db("SELECT id, username, full_name, total_xp, level, badges_count FROM users WHERE role = 'student' ORDER BY total_xp DESC LIMIT 10")
    return [dict(r) for r in rows]

@app.get("/schedules/me", tags=["Study Planning"])
async def get_my_schedules(user_id: int = Depends(get_current_user)):
    rows = query_db("SELECT * FROM schedules WHERE user_id = ?", (user_id,))
    return [dict(r) for r in rows]

@app.post("/schedules/me", tags=["Study Planning"])
async def add_my_schedule(item: ScheduleItem, user_id: int = Depends(get_current_user)):
    query_db("INSERT INTO schedules (user_id, task, time, duration, strict_mode) VALUES (?, ?, ?, ?, ?)", 
             (user_id, item.task, item.time, item.duration, 1 if item.strict_mode else 0))
    return {"success": True}

@app.delete("/schedules/{schedule_id}", tags=["Study Planning"])
async def delete_my_schedule(schedule_id: int, user_id: int = Depends(get_current_user)):
    query_db("DELETE FROM schedules WHERE id = ? AND user_id = ?", (schedule_id, user_id))
    return {"success": True}

# --- STATIC FILES AS LAST RESORT ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_PATH = os.path.join(os.path.dirname(CURRENT_DIR), "web")
if not os.path.exists(WEB_PATH): WEB_PATH = os.path.join(CURRENT_DIR, "web")

@app.get("/docs", include_in_schema=False)
async def scalar_html():
    return get_scalar_api_reference(openapi_url=app.openapi_url, title=app.title)

@app.get("/", include_in_schema=False)
async def read_index():
    idx = os.path.join(WEB_PATH, "index.html")
    return FileResponse(idx) if os.path.exists(idx) else {"msg": "Neuralis Online"}

if os.path.exists(WEB_PATH):
    app.mount("/", StaticFiles(directory=WEB_PATH), name="static")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("server:app", host="0.0.0.0", port=port)
