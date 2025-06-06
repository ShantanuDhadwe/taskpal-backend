from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
import datetime

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime.datetime] = None
    weight: int = 1
    parent_id: Optional[int] = None

class TaskCreate(TaskBase):
    pass

class TaskUpdate(TaskBase):
    pass

class Task(TaskBase):
    id: int
    priority_score: int
    subtasks: List['Task'] = Field(default_factory=list)

Task.model_rebuild()  # Needed for recursive types

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    id: int
    email: EmailStr

class Token(BaseModel):
    access_token: str
    token_type: str