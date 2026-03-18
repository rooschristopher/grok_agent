r

Autonomous coding agent with TDD, code gen, refactor tools.

## Quickstart
```bash
uv sync  # Deps
make     # Lint/test/format
make tdd-demo  # Demo TDD!
```

## Key Tools (`tools/`)
- **tdd.py**: Grok-powered TDD cycle (Red → Green → Refactor).
  ```bash
  python tools/tdd.py --spec "Your feature spec" --module my.module --max-iters 10
  ```
- code_gen.py, debug.py, refactor.py: Similar AI helpers.

## Workflow
- `make test`: Pytest all.
- `make lint`: Ruff fixes.
- `make format`: Black.

## Env
- `XAI_API_KEY`: For Grok.
- `GROK_MODEL`: Default grok-beta.

Extend with agent.py, voice.py, chats/ logs.

Happy coding! 🚀