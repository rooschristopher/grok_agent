import pytest
from pathlib import Path
from agent import Agent

def test_agent_initialization(tmp_path):
    agent = Agent(target_dir=tmp_path)
    assert agent.target_dir.resolve() == tmp_path.resolve()
    assert len(agent.tools) == 8

@pytest.fixture
def mock_xai(monkeypatch):
    class MockMsg:
        tool_calls = None
        content = "FINAL ANSWER: task completed"

    class MockChat:
        def __init__(self, model, tools):
            self.model = model
            self.tools = tools
            self.messages = []

        def append(self, msg):
            self.messages.append(msg)

        def sample(self):
            return MockMsg()

    class MockChatCreator:
        def create(self, model, tools):
            return MockChat(model, tools)

    class MockClient:
        chat = MockChatCreator()

    monkeypatch.setattr('xai_sdk.Client', lambda *args, **kwargs: MockClient())
    monkeypatch.setattr('agent.Client', lambda *args, **kwargs: MockClient())

def test_agent_run_no_tools(mock_xai, tmp_path, capsys):
    agent = Agent(target_dir=tmp_path)
    agent.run("Describe the project briefly.", max_steps=1)
    captured = capsys.readouterr()
    assert "FINAL RESPONSE:" in captured.out
    assert "FINAL ANSWER: task completed" in captured.out

def test_agent_tool_loop(mock_xai, tmp_path):
    agent = Agent(target_dir=tmp_path)
    agent.run("List files", max_steps=2)

def test_log_benchmark(tmp_path):
    agent = Agent(target_dir=tmp_path)
    agent._goal = "test goal"
    runtime = 1.23
    steps = 5
    success = True
    agent.log_benchmark(runtime, steps, success)
    benchmarks_dir = tmp_path / "benchmarks"
    runs_file = benchmarks_dir / "runs.jsonl"
    assert runs_file.exists()
    lines = runs_file.read_text().strip().split("\n")
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert abs(entry['runtime'] - runtime) < 0.01
    assert entry['steps'] == steps
    assert entry['success'] == success
    assert len(entry['goal_id']) == 8
    assert entry['goal_snippet'] == "test goal"
