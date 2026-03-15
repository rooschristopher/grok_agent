# AI Agent Toolkit (Daily Changes 2026-03-06)

Autonomous coding agent with TDD, code gen, refactor tools.

## Quickstart
```bash
cp .env.example .env  # Copy and add your API keys!
uv sync  # Deps
make     # Lint/test/format
make tdd-demo  # Demo TDD!
```

## Key Tools (`tools/`)
- **tdd.py**: Grok-powered TDD cycle (Red → Green → Refactor).
  ```bash
  python tools/tdd.py --spec \"Your feature spec\" --module my.module --max-iters 10
  ```
- code_gen.py, debug.py, refactor.py: Similar AI helpers.

## Workflow
- `make test`: Pytest all.
- `make lint`: Ruff fixes.
- `make format`: Black.

## Environment Variables
Copy `.env.example` to `.env` and fill in:

- `XAI_API_KEY`: **Required**. Grok API from [console.x.ai](https://console.x.ai).
- `SERPER_API_KEY`: **Required** for `web_search`. Free at [serper.dev](https://serper.dev).
- `GROK_MODEL`: Optional (default: `grok-4-1-fast-reasoning`).

## Extend
Use `agent.py`, `voice.py`, `chats/` logs.

Happy coding! 🚀