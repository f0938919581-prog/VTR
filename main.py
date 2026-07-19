from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from typing import List

# 1. 資料庫連線設定 (讀取 Render 設定的環境變數)
DATABASE_URL = os.environ.get("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 2. 定義資料庫模型
class EmployeeDB(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    department = Column(String)

class TaskDB(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    status = Column(String)

# 建立資料表
Base.metadata.create_all(bind=engine)

app = FastAPI()

# 3. 員工系統 API
@app.post("/employees/")
def register_employee(name: str, department: str):
    db = SessionLocal()
    new_emp = EmployeeDB(name=name, department=department)
    db.add(new_emp)
    db.commit()
    db.refresh(new_emp)
    db.close()
    return {"message": "員工已寫入資料庫", "id": new_emp.id}

@app.get("/employees/")
def get_employees():
    db = SessionLocal()
    employees = db.query(EmployeeDB).all()
    db.close()
    return employees

# 4. 任務管理 API
@app.post("/tasks/")
def add_task(title: str, status: str = "進行中"):
    db = SessionLocal()
    new_task = TaskDB(title=title, status=status)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    db.close()
    return {"message": "任務已記錄", "task_id": new_task.id}

@app.get("/tasks/")
def get_tasks():
    db = SessionLocal()
    tasks = db.query(TaskDB).all()
    db.close()
    return tasks

@app.put("/tasks/{task_id}")
def update_task_status(task_id: int, new_status: str):
    db = SessionLocal()
    task = db.query(TaskDB).filter(TaskDB.id == task_id).first()
    if not task:
        db.close()
        raise HTTPException(status_code=404, detail="找不到該任務")
    task.status = new_status
    db.commit()
    db.close()
    return {"message": "任務狀態已更新"}