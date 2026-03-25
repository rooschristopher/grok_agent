# Grok Agent: Core + Interfaces Plan

## 🎯 Goal
**Single persistent agent core** process (tools/subagents/memory).
**Multiple interfaces** (Web GUI, CLI) connect/view/control – no restart chats.

## 🏗️ Architecture
```
[Core Agent] <--Redis Stream/State--> [Web GUI (FastAPI/HTMX Live Output)]
                            |
                            --> [CLI (rich terminal stream)]
Tailscale remote access.
```

## 📦 Tech
- **Core**: agent.py → loop listen tasks, exec → stream output/state.
- **Comm**: Redis (pub events, stream chat/history).
- **Web**: FastAPI + HTMX (live chat/output, task input).
- **CLI**: rich live display connect Redis.
- uv add redis aioredis rich

## 🚀 Phases

### Phase 1: Core Agent w/ Redis
- agent.py: Redis sub tasks/goals, exec (think/tools), pub output/history/FINAL.
- Commit: `feat(core-redis): agent redis comm`

### Phase 2: Web Interface
- web/ main.py FastAPI: /chat hx-post task → pub to redis, hx-stream agent output.
- Dark Tailwind console (like agent-manager): Chat box, live stream, history.
- Commit: `feat(web-gui): HTMX live agent interface`

### Phase 3: CLI Interface
- cli.py: Connect Redis, live print output (rich statusbar).
- Commit: `feat(cli): rich terminal interface`

### Phase 4: Multi + Control
- Pause/resume agent, spawn subagents via interfaces.
- Persistent memory (chromadb).
- Tailscale docs.
- Commit: `feat(multi-control): pause/subagents`

## ⚙️ Run
```bash
uv sync
redis-server &  # Or docker
uv run agent.py  # Core
uv run web/main:app  # GUI localhost:8080
uv run cli.py  # Terminal
```

**Phase 1 now?** Redis core agent? 🚀