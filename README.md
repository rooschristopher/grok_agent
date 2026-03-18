# Grok Agent 🚀
[![Python](https://img.shields.io/badge/Python-3.12%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Grok](https://img.shields.io/badge/Powered%20by-Grok%20AI-orange)](https://grok.x.ai/)

## 🌟 What is Grok Agent?
Grok Agent is an **autonomous AI coding assistant** powered by Grok (from xAI). It helps you:
- Write, test, debug, and refactor code **automatically** using TDD (Test-Driven Development).
- Spawn **sub-agents** for parallel tasks.
- Search the web, run shell commands, manage git, and more via **powerful tools**.
- Persist chats, memory, and costs for long-running projects.

Perfect for developers who want AI to handle the grunt work!

## 👥 Who is this for?
- Beginners: Step-by-step setup—no prior experience needed.
- Pros: Advanced tools for rapid prototyping and production code.

## 📋 Prerequisites (5 minutes setup)
1. **GitHub Account**: [Sign up free](https://github.com/signup).
2. **Python 3.12+**: Download from [python.org](https://www.python.org/downloads/).
3. **uv** (fast Python manager): 
   ```bash
   pip install uv  # Or brew install uv on Mac
   ```
4. **XAI API Key** (free tier available):
   - Go to [console.x.ai](https://console.x.ai/), sign up/login.
   - Create API key → Copy it (keep secret!).

**No Docker, no cloud setup needed—runs locally!**

## 🚀 Quickstart (Copy-Paste Ready)
1. **Download/Clone the repo**:
   - Click **Code > Download ZIP** (or use GitHub Desktop).
   - **OR** (if using terminal):
     ```bash
     git clone https://github.com/rooschristopher/grok_agent.git  # Replace with actual repo URL
     cd grok_agent
     ```

2. **Install dependencies**:
   ```bash
   uv sync
   ```

3. **Set your API key**:
   - Copy `.env.example` to `.env` (if exists) or create `.env`:
     ```
     XAI_API_KEY=your_key_here
     GROK_MODEL=grok-beta  # Optional, default
     ```
   - **Never commit .env** (it's in .gitignore!).

4. **Run the demo**:
   ```bash
   make tdd-demo  # Watches AI do TDD magic!
   ```
   Or lint/test everything:
   ```bash
   make  # Lint + test + format
   ```

🎉 You're live! Chat with the agent via `python chat.py` or `agent.py`.

## 🛠️ Key Tools (in `tools/`)
| Tool | Description | Example |
|------|-------------|---------|
| **tdd.py** | Grok-powered TDD: Red → Green → Refactor. | `python tools/tdd.py --spec \"Add fizzbuzz\" --module fizzbuzz --max-iters 10` |
| **code_gen.py** | Generate code from specs. | `python tools/code_gen.py --prompt \"Build a CLI calculator\"` |
| **debug.py** | AI debugging wizard. | `python tools/debug.py --file buggy.py --error \"traceback here\"` |
| **refactor.py** | Smart refactoring. | `python tools/refactor.py --file old.py --goal \"Make async\"` |
| **git/**, **github/**, **jira/** | Git ops, GitHub issues, Jira integration. | See tool docs. |

Full agent tools: Shell, web search, subagents, file I/O, git status/commit/push.

## 🔄 Development Workflow
```bash
make test    # Run pytest
make lint    # Ruff auto-fix
make format  # Black format
make all     # Everything!
```

## ⚙️ Environment Variables
| Var | Default | Description |
|-----|---------|-------------|
| `XAI_API_KEY` | Required | Your xAI/Grok API key. |
| `GROK_MODEL` | `grok-beta` | Model to use (e.g., `grok-2`). |

## 🚀 Advanced Features
- **Spawn subagents**: Parallel tasks (e.g., research + code).
- **Voice mode**: `python voice.py`.
- **Persistent memory**: Chats/logs in `chats/`, `chromadb/`.
- **Costs tracking**: `costs.jsonl`.

Extend via `agent.py` or build your own tools.

## 🐛 Troubleshooting
- **uv not found?** `pipx install uv`.
- **API errors?** Check key in `.env`.
- **Tests fail?** `make lint` first.
- **Mac/Linux only?** Windows: Use WSL.

## 🤝 Contributing
1. Fork → Clone → Branch.
2. `make` to setup.
3. Commit → PR!

## 📄 License
MIT—use freely!

Happy coding! Questions? Open an issue or chat with me. 🎊