# app/crud.py

from sqlalchemy.orm import Session
from datetime import datetime
from . import models, schemas

def calculate_priority_score(weight, due_date):
    if not due_date:
        return 0
    now = datetime.now()
    days_until_due = (due_date - now).days
    if days_until_due < 0:
        days_until_due = 0
    return int(100 * weight / (days_until_due + 1))

def get_task(db: Session, task_id: int, user_id: int):
    return db.query(models.Task).filter(models.Task.id == task_id, models.Task.owner_id == user_id).first()

def get_subtasks(db: Session, parent_id: int, user_id: int):
    return db.query(models.Task).filter(models.Task.parent_id == parent_id, models.Task.owner_id == user_id).all()

def get_tasks(db: Session, user_id: int):
    return db.query(models.Task).filter(models.Task.owner_id == user_id).all()

def create_task(db: Session, task: schemas.TaskCreate, user_id: int):
    db_task = models.Task(**task.dict(), owner_id=user_id)
    db_task.priority_score = calculate_priority_score(db_task.weight, db_task.due_date)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

def update_task(db: Session, db_task: models.Task, task_update: schemas.TaskUpdate):
    update_data = task_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_task, key, value)
    db_task.priority_score = calculate_priority_score(db_task.weight, db_task.due_date)
    db.commit()
    db.refresh(db_task)
    return db_task

def delete_task(db: Session, db_task: models.Task):
    db.delete(db_task)
    db.commit()

def get_top_urgent_tasks(db: Session, user_id: int, top_n=5):
    return (
        db.query(models.Task)
        .filter(models.Task.owner_id == user_id)
        .order_by(models.Task.priority_score.desc())
        .limit(top_n)
        .all()
    )