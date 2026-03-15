import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from agent import Agent

@pytest.fixture(autouse=True)
def mock_globals(monkeypatch):
    monkeypatch.setattr("agent.load_dotenv", Mock())
    monkeypatch.setattr("agent.setup_logging", Mock())
    monkeypatch.setattr("agent.get_logger", lambda name: Mock())
    monkeypatch.setattr("agent.os.getenv", lambda key: "fake_key")

@pytest.fixture
def agent(tmp_path, monkeypatch):
    monkeypatch.setattr("agent.Client", MagicMock())
    monkeypatch.setattr("agent.uuid.uuid4", Mock(return_value="test-uuid"))
    agent_ = Agent(target_dir=str(tmp_path))
    agent_.shared_dir = tmp_path / "agent_shared"
    yield agent_

class TestAgent:
    def test_init(self, agent, tmp_path):
        assert agent.target_dir == tmp_path.resolve()
        assert agent.model == "grok-4-1-fast-reasoning"
        assert agent.agent_id == "test-uuid"
        assert len(agent.tools) > 0

    def test_list_dir(self, agent, tmp_path):
        (tmp_path / "file1.txt").touch()
        (tmp_path / "dir1").mkdir()
        result = agent.list_dir(".")
        data = json.loads(result)
        assert data["path"] == str(tmp_path.resolve())
        assert sorted(data["items"]) == ["dir1", "file1.txt"]
        result = agent.list_dir("nonexist")
        data = json.loads(result)
        assert "error" in data

    def test_read_file(self, agent, tmp_path):
        test_content = "hello world"
        (tmp_path / "test.txt").write_text(test_content)
        result = agent.read_file("test.txt")
        assert result == test_content
        result = agent.read_file("missing.txt")
        data = json.loads(result)
        assert "missing.txt" in data["error"]

    def test_write_file(self, agent, tmp_path):
        result = agent.write_file("new.txt", "hello")
        data = json.loads(result)
        assert data["status"] == "ok"
        assert (tmp_path / "new.txt").read_text() == "hello"
        result = agent.write_file("new.txt", " world", append=True)
        data = json.loads(result)
        assert data["status"] == "ok"
        assert (tmp_path / "new.txt").read_text() == "hello world"
        result = agent.write_file("sub/new.txt", "sub content")
        data = json.loads(result)
        assert data["status"] == "ok"
        assert (tmp_path / "sub/new.txt").read_text() == "sub content"

    def test_run_shell(self, agent, tmp_path):
        with patch("agent.subprocess.run") as mock_run:
            mock_run.return_value = Mock(stdout="mock out", stderr="mock err", returncode=0)
            result = agent.run_shell("echo test")
            data = json.loads(result)
            assert data["stdout"] == "mock out"
            mock_run.assert_called_once_with(
                "echo test", shell=True, capture_output=True, text=True, timeout=30, cwd=str(agent.target_dir)
            )

    def test_web_search(self, agent):
        with patch("agent.requests.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.raise_for_status.return_value = None
            mock_resp.json.return_value = {
                "organic": [{"title": "Test", "snippet": "test", "link": "http://test"}]
            }
            mock_post.return_value = mock_resp
            result = agent.web_search("test query", 1)
            data = json.loads(result)
            assert data["query"] == "test query"
            assert len(data["raw_results"]) == 1
        with patch("agent.os.getenv", return_value=None):
            result = agent.web_search("query")
            data = json.loads(result)
            assert "SERPER_API_KEY not set" in data["error"]
