from fastapi import FastAPI, Depends, Request, Form
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from uuid import uuid4
from .schemas import NodeCreate, NodeResponse, TaskCreate, TaskResponse
from .db import get_db, NodeDB, TaskDB, Base, engine

app = FastAPI(title='Swarm Cluster')
templates = Jinja2Templates('templates')

@app.on_event("startup")
def init_db():
    Base.metadata.create_all(bind=engine)

@app.get("/")
def dashboard(request: Request, db: Session = Depends(get_db)):
    nodes = db.query(NodeDB).all()
    tasks = db.query(TaskDB).all()
    return templates.TemplateResponse("dashboard.html", {"request": request, "nodes": nodes, "tasks": tasks})

@app.get("/api/nodes")
def list_nodes(db: Session = Depends(get_db)):
    nodes = db.query(NodeDB).all()
    return [NodeResponse.model_validate(n) for n in nodes]

@app.post("/api/nodes")
def create_node(node: NodeCreate, db: Session = Depends(get_db)):
    db_node = db.query(NodeDB).filter(NodeDB.id == node.id).first()
    if db_node:
        db_node.status = "idle"
    else:
        db_node = NodeDB(id = node.id, status="idle")
        db.add(db_node)
    db.commit()
    if not hasattr(db_node, 'id'):  # if new
        db.refresh(db_node)
    return NodeResponse.model_validate(db_node)

@app.post("/api/register")
def register_node(node: NodeCreate, db: Session = Depends(get_db)):
    return create_node(node, db)

@app.get("/api/tasks")
def list_tasks(db: Session = Depends(get_db)):
    tasks = db.query(TaskDB).all()
    return [TaskResponse.model_validate(t) for t in tasks]

@app.post("/api/tasks")
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    new_id = str(uuid4())
    db_task = TaskDB(id=new_id, title=task.title)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return TaskResponse.model_validate(db_task)

@app.post("/api/claim/{task_id}")
def claim_task(task_id: str, node_id: str = Form(...), db: Session = Depends(get_db)):
    task = db.query(TaskDB).filter(TaskDB.id == task_id, TaskDB.status == "pending").first()
    if task:
        task.node_id = node_id
        task.status = "in_progress"
        db.commit()
        return {"status": "claimed", "task_id": task_id}
    return {"error": "Task not available"}

@app.post("/api/update/{task_id}")
def update_task(task_id: str, status: str = Form(...), history_json: str = Form(...), db: Session = Depends(get_db)):
    task = db.query(TaskDB).filter(TaskDB.id == task_id).first()
    if task:
        task.status = status
        task.history_json = history_json
        db.commit()
        return {"status": "updated", "task_id": task_id}
    return {"error": "Task not found"}