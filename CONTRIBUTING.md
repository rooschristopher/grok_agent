# Contributing

Thanks for considering contributing to **Learning Assistant**!

## Development Workflow

1. **Fork & Clone**
   ```bash
   git clone &lt;your-fork&gt;
   cd Learning_Assistant
   git checkout -b feat/your-feature
   ```

2. **Setup**
   ```bash
   pip install -e .
   ```

3. **Tickets**
   - Check `tickets/` for pending
   - Follow TDD cycle in ticket .md

4. **Test Driven Development (TDD)**
   - **Red**: Write failing test
   - **Green**: Make it pass (minimal)
   - **Refactor**: Improve code
   - Run `pytest tests/ -v` → all green
   - Move ticket to `tickets/completed/`

5. **Lint**
   ```bash
   ruff check .
   ruff format .
   ```

6. **Commit**
   Use [Conventional Commits](https://www.conventionalcommits.org/):
   ```
   feat: add new tool test
   fix: resolve append bug
   docs: update README
   ```

7. **Push & PR**
   ```bash
   git push origin feat/your-feature
   ```
   Open PR to main.

## Using the Agent
The easiest way:
```bash
python agent.py
```
Agent will process tickets autonomously!

## Issues & Questions
- [Open Issue](https://github.com/user/repo/issues/new)
- Ping @croos