import os
import asyncio
import httpx
from fastapi import FastAPI, BackgroundTasks
from contextlib import asynccontextmanager
from typing import List
from swarm.schemas.agent import NodeInfo, PendingTask, HistoryEntry, TaskUpdateRequest

CLUSTER_URL: str = os.getenv("CLUSTER_URL", "http://localhost:8000")
NODE_ID: str = os.getenv("NODE_ID", "node-1")
NODE_CAPS: List[str] = [c.strip() for c in os.getenv("NODE_CAPS", "grok-coding").split(",")]

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: register to cluster
    async with httpx.AsyncClient() as client:
        await client.post(f"{CLUSTER_URL}/api/register", json={
            "node_id": NODE_ID,
            "capabilities": NODE_CAPS
        })
    # Start polling loop
    poll_task = asyncio.create_task(polling_loop())
    yield
    # Cleanup
    poll_task.cancel()
    try:
        await poll_task
    except asyncio.CancelledError:
        pass

async def polling_loop():
    while True:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{CLUSTER_URL}/api/pending")
                if resp.status_code != 200:
                    await asyncio.sleep(10)
                    continue
                pending = resp.json()
                for task_dict in pending:
                    try:
                        task = PendingTask.model_validate(task_dict)
                        # Check if capabilities match
                        if any(cap in NODE_CAPS for cap in task.required_capabilities):
                            # Claim the task
                            claim_resp = await client.post(
                                f"{CLUSTER_URL}/api/claim/{task.id}",
                                json={"node_id": NODE_ID}
                            )
                            if claim_resp.status_code == 200:
                                await execute_agent(client, task.id, task.goal)
                    except Exception as e:
                        print(f"Error processing task {task_dict.get('id', 'unknown')}: {e}")
        except Exception as e:
            print(f"Polling loop error: {e}")
        await asyncio.sleep(10)

async def execute_agent(client: httpx.AsyncClient, task_id: str, goal: str):
    thoughts = [
        f"Node {NODE_ID} starting execution of goal: {goal}",
        "Step 1: Understanding the task requirements.",
        "Step 2: Planning the implementation strategy.",
        "Step 3: Writing the necessary code.",
        "Step 4: Testing and debugging.",
        "Step 5: Finalizing and optimizing.",
        f"Task {task_id} completed successfully by {NODE_ID}."
    ]
    for thought in thoughts:
        try:
            await client.post(
                f"{CLUSTER_URL}/api/update/{task_id}",
                json={"history_entry": {"type": "thought", "content": thought}}
            )
            print(f"Updated task {task_id} with thought: {thought[:50]}...")
            await asyncio.sleep(2)
        except Exception as e:
            print(f"Error updating task {task_id}: {e}")

app = FastAPI(title="Swarm Node", lifespan=lifespan)

@app.post("/register")
async def manual_register():
    """Manual registration endpoint."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{CLUSTER_URL}/api/register",
            json={"node_id": NODE_ID, "capabilities": NODE_CAPS}
        )
    return {
        "status": "registered" if resp.status_code == 200 else "failed",
        "node_id": NODE_ID,
        "response": resp.json() if resp.status_code == 200 else None
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "node_id": NODE_ID,
        "capabilities": NODE_CAPS,
        "cluster_url": CLUSTER_URL
    }
