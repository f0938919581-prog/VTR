import uuid
from datetime import datetime
import bcrypt
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, Session

# ==========================================
# 1. 資料庫設定 (與先前相同)
# ==========================================
engine = create_engine('sqlite:///xingyao_db.sqlite', connect_args={"check_same_thread": False})
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class User(Base):
    __tablename__ = 'users'
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    audit_logs = relationship("AuditLog", back_populates="user")

class AuditLog(Base):
    __tablename__ = 'audit_logs'
    log_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id'))
    action = Column(String(50), nullable=False)
    ip_address = Column(String(45))
    details = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="audit_logs")

Base.metadata.create_all(engine)

# ==========================================
# 2. 定義 API 請求的資料格式 (Pydantic)
# ==========================================
class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    full_name: str

# 取得資料庫連線的依賴函式
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==========================================
# 3. 建立 FastAPI 應用程式與端點
# ==========================================
app = FastAPI(title="星耀科技 - 個資管理 API", description="核心個資系統後端", version="1.0")

@app.post("/api/register", summary="註冊新使用者")
def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
    # 檢查帳號或 Email 是否已存在
    existing_user = db.query(User).filter((User.username == user_in.username) | (User.email == user_in.email)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="帳號或 Email 已經被註冊過了")

    # 密碼加密
    salt = bcrypt.gensalt()
    hashed_pwd = bcrypt.hashpw(user_in.password.encode('utf-8'), salt).decode('utf-8')

    # 建立使用者
    new_user = User(
        username=user_in.username,
        email=user_in.email,
        password_hash=hashed_pwd,
        full_name=user_in.full_name
    )
    db.add(new_user)
    db.flush() 

    # 建立稽核日誌
    audit_log = AuditLog(
        user_id=new_user.id,
        action='REGISTER_USER',
        ip_address='127.0.0.1', # 實務上可從 FastAPI 的 Request 中取得真實 IP
        details={"email_used": user_in.email, "client": "web_api"}
    )
    db.add(audit_log)
    db.commit()

    return {
        "status": "success",
        "message": f"成功註冊使用者：{new_user.full_name}",
        "user_id": new_user.id
    }
if __name__ == "__main__":
    import uvicorn
    # 讓程式自己喚醒伺服器，打包成 EXE 後連按兩下就能直接運行
    uvicorn.run(app, host="127.0.0.1", port=8000)
# 修改前：engine = create_engine('sqlite:///xingyao_db.sqlite')
# 修改後：請換成您的 Supabase 連線字串
DATABASE_URL = "postgresql://postgres:您的密碼@db.您的專案ID.supabase.co:5432/postgres"

from sqlalchemy import create_engine
engine = create_engine(DATABASE_URL)