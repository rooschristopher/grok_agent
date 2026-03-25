from pydantic import BaseModel, ConfigDict
from typing import Optional

class NodeCreate(BaseModel):
    id: str

class NodeResponse(BaseModel):
    id: str
    status: str
    model_config = ConfigDict(from_attributes=True)

class TaskCreate(BaseModel):
    title: str

class TaskResponse(BaseModel):
    id: str
    title: str
    status: str
    node_id: Optional[str] = None
    history_json: str = "[]"
    model_config = ConfigDict(from_attributes=True)