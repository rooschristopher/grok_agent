from pydantic import BaseModel
from typing import List

class NodeInfo(BaseModel):
    node_id: str
    capabilities: List[str]

class PendingTask(BaseModel):
    id: str
    goal: str
    required_capabilities: List[str]

class HistoryEntry(BaseModel):
    type: str
    content: str

class TaskUpdateRequest(BaseModel):
    history_entry: HistoryEntry