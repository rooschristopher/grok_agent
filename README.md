# AI Agent Toolkit ✨ Coverage Badges

[![CI](https://github.com/rooschristopher/grok_agent/workflows/CI/badge.svg?branch=develop)](https://github.com/rooschristopher/grok_agent/actions)

![pytest-coverage](coverage.svg)

Autonomous coding agent with TDD, code gen, refactor tools.

## Quickstart
```bash
uv sync --extra full  # Deps
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
- `make update-coverage-badge`: Update cov badge in README.

## Env
- `XAI_API_KEY`: For Grok.
- `GROK_MODEL`: Default grok-beta.

Extend with agent.py, voice.py, chats/ logs.

Happy coding! 🚀
