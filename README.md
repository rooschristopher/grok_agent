# AI Agent Toolkit

Autonomous coding agent with TDD, code gen, refactor tools. Powered by xAI Grok.

## Quickstart 🚀
```bash
cp .env.example .env  # Edit .env with your API keys!
uv sync               # Install dependencies
make                  # Lint, test, format
make tdd-demo         # Try TDD demo!
```

## Key Tools (`tools/`)
- **tdd.py** 🔴➜🟢➜🔄: Grok-powered TDD (Red → Green → Refactor).
  ```bash
  python tools/tdd.py --spec \"Your feature spec here\" --module my.module --max-iters 10
  ```
- `code_gen.py`, `debug.py`, `refactor.py`: AI-assisted coding.

## Workflow
| Command | Action |
|---------|--------|
| `make test` | Pytest all 🔬 |
| `make lint` | Ruff auto-fix 🧹 |
| `make format` | Black 🖌️ |

## Env Setup 🛠️
1. `cp .env.example .env`
2. Edit `.env` (use editor of choice).
3. Restart/reload.

**Required:**
- `XAI_API_KEY`: [console.x.ai](https://console.x.ai)

**Recommended:**
- `SERPER_API_KEY`: [serper.dev](https://serper.dev) - Free tier for `web_search` tool.

**Optional:**
- `VOICE_TESTING_KEY`: Voice features.
- `JIRA_API_KEY`: Jira integration.
- `XAI_MANAGEMENT_API_KEY`: Advanced xAI.

**Defaults:**
- `GROK_MODEL=grok-beta`

Full list in `.env.example`.

## Extend
- `agent.py`: Core agent.
- `voice.py`: Voice I/O.
- `chats/`: Conversation logs.

Happy coding! 🎉