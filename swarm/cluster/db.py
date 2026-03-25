import aiosqlite
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import uuid4
from pydantic import BaseModel

class Node(BaseModel):
    id: str
    status: str = "active"
    capabilities: List[str] = []

class TaskCreate(BaseModel):
    data: Dict[str, Any]

class Task(BaseModel):
    id: str
    status: str
    node_id: Optional[str] = None
    data: Dict[str, Any]
    history: List[Dict[str, Any]] = []
    created_at: str
    updated_at: str

async def init_db(db_path: str = "cluster.db") -> None:
    async with aiosqlite.connect(db_path) as db:
        await db.execute(&quot;&quot;&quot;
            CREATE TABLE IF NOT EXISTS nodes (
                id TEXT PRIMARY KEY,
                status TEXT NOT NULL DEFAULT 'active',
                capabilities TEXT,
                last_seen TEXT NOT NULL DEFAULT (datetime('now')),
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
        &quot;&quot;&quot;)
        await db.execute(&quot;&quot;&quot;
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                status TEXT NOT NULL DEFAULT 'pending',
                node_id TEXT,
                data TEXT NOT NULL,
                history TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY(node_id) REFERENCES nodes(id)
            );
        &quot;&quot;&quot;)
        await db.commit()

async def register_node(node: Node, db_path: str = "cluster.db") -> None:
    capabilities_json = json.dumps(node.capabilities)
    now = datetime.now().isoformat()
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            &quot;&quot;&quot;
            INSERT OR REPLACE INTO nodes (id, status, capabilities, last_seen, created_at)
            VALUES (?, ?, ?, ?, COALESCE((SELECT created_at FROM nodes WHERE id=?), ?))
            &quot;&quot;&quot;,
            (node.id, node.status, capabilities_json, now, node.id, now)
        )
        await db.commit()

async def get_nodes(db_path: str = "cluster.db") -> List[Node]:
    async with aiosqlite.connect(db_path) as db:
        async with db.execute("SELECT id, status, capabilities FROM nodes") as cursor:
            rows = await cursor.fetchall()
            return [
                Node(
                    id=row[0],
                    status=row[1],
                    capabilities=json.loads(row[2]) if row[2] else []
                )
                for row in rows
            ]

async def create_task(task_create: TaskCreate, db_path: str = "cluster.db") -> Task:
    task_id = str(uuid4())
    data_json = json.dumps(task_create.data)
    now = datetime.now().isoformat()
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            &quot;&quot;&quot;
            INSERT INTO tasks (id, data, history, created_at, updated_at)
            VALUES (?, ?, '[]', ?, ?)
            &quot;&quot;&quot;,
            (task_id, data_json, now, now)
        )
        await db.commit()
    return Task(
        id=task_id,
        status="pending",
        data=task_create.data,
        node_id=None,
        history=[],
        created_at=now,
        updated_at=now
    )

async def get_pending_tasks(db_path: str = "cluster.db") -> List[Task]:
    async with aiosqlite.connect(db_path) as db:
        async with db.execute(
            "SELECT id, status, node_id, data, history, created_at, updated_at "
            "FROM tasks WHERE status = 'pending' ORDER BY created_at ASC"
        ) as cursor:
            rows = await cursor.fetchall()
            tasks = []
            for row in rows:
                tasks.append(
                    Task(
                        id=row[0],
                        status=row[1],
                        node_id=row[2],
                        data=json.loads(row[3]),
                        history=json.loads(row[4]),
                        created_at=row[5],
                        updated_at=row[6]
                    )
                )
            return tasks

async def claim_task(task_id: str, node_id: str, db_path: str = "cluster.db") -> bool:
    now = datetime.now().isoformat()
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "UPDATE tasks SET status = 'claimed', node_id = ?, updated_at = ? WHERE id = ? AND status = 'pending'",
            (node_id, now, task_id)
        )
        await db.commit()
        return db.total_changes > 0

async def update_task(
    task_id: str, status: str, history_entry: Optional[Dict[str, Any]] = None, db_path: str = "cluster.db"
) -> bool:
    now = datetime.now().isoformat()
    async with aiosqlite.connect(db_path) as db:
        if history_entry:
            cursor = await db.execute("SELECT history FROM tasks WHERE id = ?", (task_id,))
            row = await cursor.fetchone()
            if not row:
                return False
            history = json.loads(row[0])
            history.append({**history_entry, "timestamp": now})
            history_json = json.dumps(history)
            await db.execute(
                "UPDATE tasks SET status = ?, history = ?, updated_at = ? WHERE id = ?",
                (status, history_json, now, task_id)
            )
        else:
            await db.execute(
                "UPDATE tasks SET status = ?, updated_at = ? WHERE id = ?",
                (status, now, task_id)
            )
        await db.commit()
        return db.total_changes > 0
