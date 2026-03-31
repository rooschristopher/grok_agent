import pytest
from fastapi.testclient import TestClient
from web.main import app

client = TestClient(app)

def test_get_root_returns_html():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert '<title>Grok Agent</title>' in response.text
    assert "Grok Agent 🚀" in response.text
    assert "htmx.org" in response.text
    assert "tailwindcss.com" in response.text
    assert 'hx-post="/chat"' in response.text
    assert '&lt;title&gt;' not in response.text  # Plain HTML, no entities

def test_post_chat_success():
    task = "test task"
    response = client.post("/chat", data={"task": task})
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Task: " in response.text
    assert task in response.text
    assert "Executing..." in response.text
    assert "setTimeout" in response.text

def test_post_chat_missing_task():
    response = client.post("/chat", data={})
    assert response.status_code == 422
    assert "field required" in response.text.lower()
