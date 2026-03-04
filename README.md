# Grok Agent 🚀🤖

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/Tests-passing-brightgreen.svg)](https://pytest.org/)

**Much better autonomous coding agent** powered by [xAI Grok](https://x.ai/) with enhanced tools, Streamlit UI, memory support, and TDD workflow.

## 🚀 New Features (Improvements over Learning Assistant)
- **Streamlit Chat UI** (`streamlit run chat_ui.py`)
- **New Tools**: `run_tests`, `run_lint`, `git_status`
- **Memory**: ChromaDB integration (TBD)
- **Better CLI** with Typer/Rich
- **Docker support** (TBD)
- **Improved subagent management**
- **Voice** enhanced

## 📦 Installation
```bash
cd ~/work/ai/grok_agent
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Set keys in `.env`:
```
XAI_API_KEY=your_xai_key
SERPER_API_KEY=your_serper_key  # optional for web_search
```

## 🚀 Quick Start

### Chat UI ⭐
```bash
streamlit run chat_ui.py
```
http://localhost:8501 - Enter goal, visualize tools & subagents!

### CLI
```bash
python agent.py --goal "Your goal"
```

## 🛠️ Tools (Enhanced)
... (same + new)

## Next: Run `pytest`, `ruff check .`, explore!