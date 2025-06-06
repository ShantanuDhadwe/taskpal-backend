from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware

from app import models, schemas, crud, database, auth, dependencies

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from .dependencies import get_db, get_current_user

def build_hierarchy(parent, all_tasks):
    children = [t for t in all_tasks if t.parent_id == parent.id]
    subtasks = [build_hierarchy(c, all_tasks) for c in children]
    task_dict = {col: getattr(parent, col) for col in parent.__table__.columns.keys()}
    task_dict['subtasks'] = subtasks
    return schemas.Task(**task_dict)



@app.post("/register", response_model=schemas.User)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = auth.get_user_by_email(db, user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = auth.get_password_hash(user.password)
    user_obj = models.User(email=user.email, hashed_password=hashed_password)
    db.add(user_obj)
    db.commit()
    db.refresh(user_obj)
    return schemas.User(id=user_obj.id, email=user_obj.email)

@app.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    token = auth.create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/me", response_model=schemas.User)
def get_me(current_user: models.User = Depends(get_current_user)):
    return schemas.User(id=current_user.id, email=current_user.email)

@app.get("/tasks", response_model=list[schemas.Task])
def list_tasks(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    all_tasks = crud.get_tasks(db, current_user.id)
    root_tasks = [t for t in all_tasks if t.parent_id is None]
    return [build_hierarchy(t, all_tasks) for t in root_tasks]

@app.get("/tasks/top-urgent", response_model=list[schemas.Task])
def top_urgent_tasks(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    all_tasks = crud.get_tasks(db, current_user.id)
    urgent_tasks = crud.get_top_urgent_tasks(db, current_user.id)
    return [build_hierarchy(t, all_tasks) for t in urgent_tasks]

@app.post("/tasks", response_model=schemas.Task)
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    db_task = crud.create_task(db, task, current_user.id)
    all_tasks = crud.get_tasks(db, current_user.id)
    return build_hierarchy(db_task, all_tasks)

@app.put("/tasks/{task_id}", response_model=schemas.Task)
def update_task(task_id: int, task_update: schemas.TaskUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    db_task = crud.get_task(db, task_id, current_user.id)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    db_task = crud.update_task(db, db_task, task_update)
    all_tasks = crud.get_tasks(db, current_user.id)
    return build_hierarchy(db_task, all_tasks)


@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    db_task = crud.get_task(db, task_id, current_user.id)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    crud.delete_task(db, db_task)
    return {"ok": True}

# LLM integration router (optional)
try:
    from .llm import router as llm_router
    app.include_router(llm_router)
except ImportError:
    pass
