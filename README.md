# Grok Agent 🚀🤖

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/Tests-passing-brightgreen.svg)](https://pytest.org/)

**Much better autonomous coding agent** powered by [xAI Grok](https://x.ai/) with enhanced tools, Rich terminal chat, memory support, and TDD workflow.

## 🚀 New Features
- **Rich Terminal Chat** (`python chat.py` or `grok-chat`)
- **New Tools**: `run_tests`, `run_lint`, `git_status` (TBD)
- **Memory**: ChromaDB integration (TBD)
- **Better CLI** with Typer/Rich
- **Docker support** (TBD)
- **Improved subagent management**
- **Voice** enhanced (TBD)

## 📦 Installation
```bash
cd ~/work/ai/grok_agent
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate
pip install -e .
```

### 🔑 API Keys Setup (`.env` file)
Create or edit `.env` in the project root with your keys:

#### xAI Grok API Key (Required)
1. Sign up/log in at the [xAI Console](https://console.x.ai/) (or start at [accounts.x.ai](https://accounts.x.ai/sign-up); may require X/Twitter account).
2. Complete developer onboarding if prompted.
3. Add **credits** to your account (pay-per-use billing).
4. Navigate to **API Keys** > **Create API Key**.
5. Copy the key (starts with `xai-`).

```
XAI_API_KEY=xai-your-key-here
```

**Docs**: [xAI Quickstart](https://docs.x.ai/developers/quickstart) | [API Overview](https://x.ai/api)

#### Serper API Key (Optional, for `web_search` tool)
1. Sign up at [serper.dev](https://serper.dev) (free tier: 2,500 searches/month).
2. Copy your API key from the dashboard.

```
SERPER_API_KEY=serper-your-key-here
```

## 🚀 Quick Start

### Terminal Chat ⭐⭐
```bash
# Direct
python chat.py

# Or via entrypoint (after pip install -e .)
grok-chat
```
Beautiful Rich UI, persistent conversation memory, live tool execution visualization!

### Single Goal CLI
```bash
python agent.py --goal "Your goal here"
```

### Web UI (TBD)
```bash
streamlit run chat_ui.py  # Coming soon
```

## 🛠️ Tools
- `list_dir`, `read_file`, `write_file`, `run_shell`
- `web_search`
- `spawn_subagent`, `list_subagents`, `kill_subagent`

## Next: Run `pytest`, `ruff check .`, explore!
