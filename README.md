# Learning Assistant 🧠🤖

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/Tests-passing-brightgreen.svg)](https://pytest.org/)

**Autonomous Coding Agent** powered by [xAI Grok](https://x.ai/) with tools for filesystem operations and shell execution. Designed for TDD-driven ticket completion in project directories.

## 🚀 Features

- **Tools**: `list_dir`, `read_file`, `write_file` (append/overwrite), `run_shell`
- **TDD Workflow**: Process tickets from `tickets/` folder, move completed to `tickets/completed/`
- **Logging**: Structured logs to `app.log`
- **Voice Integration**: `voice.py` for speech (TBD)
- **Chat UI**: Web-based conversational interface (`chat_ui.py`)
- **Subagents**: Parallel task execution
- **Web Search**: Research via Serper.dev
- **Testing**: Comprehensive unit tests with pytest
- **Linting**: Ruff configured

## 📦 Installation

1. Clone the repo:
   ```bash
   git clone &lt;repo-url&gt;
   cd Learning_Assistant
   ```

2. Create virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # .venv\\Scripts\\activate  # Windows
   ```

3. Install dependencies:
   ```bash
   pip install -e .
   pip install streamlit  # Or included now
   ```

4. Set API key:
   ```bash
   echo &quot;XAI_API_KEY=your_key&quot; &gt;&gt; .env
   # Optional: SERPER_API_KEY=your_key from serper.dev
   ```

## 🚀 Quick Start

### CLI Agent
```bash
python agent.py --goal &quot;Your goal here&quot;
```

### Chat UI (Recommended)
```bash
streamlit run chat_ui.py
```
Open [http://localhost:8501](http://localhost:8501)

Interact naturally, see tool calls visualized, upload files, manage subagents.

## 🛠️ Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_dir` | List files/directories | `path` (str, optional) |
| `read_file` | Read entire file | `filename` (str, required) |
| `write_file` | Write/overwrite/append file | `filename`, `content` (str req), `append` (bool) |
| `run_shell` | Exec shell cmd | `cmd` (str req) |
| `spawn_subagent` | Spawn parallel sub-agent | `goal` (str req), `max_steps` (int opt) |
| `list_subagents` | List subagents statuses | none |
| `kill_subagent` | Kill subagent | `agent_id` (str req) |
| `web_search` | Google search | `query` (str req), `num_results` (int opt=5) |

## 📁 Project Structure

```
Learning_Assistant/
├── agent.py         # CLI agent
├── chat_ui.py       # Streamlit web UI ⭐
├── voice.py         # Voice (TBD)
├── tests/           # Tests
├── tickets/         # Pending tickets (.md)
│   ├── backlog/
│   └── completed/
├── docs/
├── pyproject.toml
└── README.md
```

## 🧪 Testing & Linting

```bash
pytest tests/ -v
ruff check .
ruff format .
```

## 🤝 Contributing

1. Add ticket to `tickets/backlog/`
2. Use Chat UI or CLI to implement
3. Move to `tickets/completed/` when done
4. Commit & PR

## 📄 License

MIT

## 🙏 Acknowledgments

- [xAI SDK](https://github.com/xai-org/xai-sdk)
- [Streamlit](https://streamlit.io/)
- [Pytest](https://pytest.org/)
- [Ruff](https://ruff.rs/)
