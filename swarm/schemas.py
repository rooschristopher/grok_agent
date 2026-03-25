from typing import List, Dict, Any
from pydantic import BaseModel


class Node(BaseModel):
    id: str
    capabilities: List[str]
    status: str


class Task(BaseModel):
    id: str
    goal: str
    status: str
    history: List[Dict[str, Any]]
    assigned_node: str


class TaskCreate(BaseModel):
    goal: str


class TaskUpdate(BaseModel):
    status: str
    history_entry: Dict[str, Any]