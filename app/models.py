# app/models.py

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base
import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    tasks = relationship("Task", back_populates="owner")

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String)
    due_date = Column(DateTime)
    weight = Column(Integer, default=1)
    priority_score = Column(Integer, default=0)
    owner_id = Column(Integer, ForeignKey("users.id"))
    parent_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    owner = relationship("User", back_populates="tasks")
    subtasks = relationship("Task", backref="parent", remote_side=[id])