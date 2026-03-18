MANDATORY WORKTREE POLICY 🛡️ (Injected into EVERY agent system prompt via agent.py)

## Core Rule (Precedence: After base &lt;policy&gt;, before goal)
**ALWAYS** use git worktrees **by default** for:
- Code generation/implementation.
- File creates/edits/deletes.
- Testing/refactoring/debugging.
- ANY dev task risking main branch pollution.

## Workflow (Step-by-Step, NO EXCEPTIONS):
1. **Check main**: `git_status` → If dirty, commit/push first.
2. **Slug task**: e.g. "add-fizzbuzz-feature" → branch `feat/add-fizzbuzz-feature`.
3. **Create WT**: 
   ```
   mkdir -p ../worktrees/slug
   git worktree add ../worktrees/slug -b feat/slug
   ```
   OR `python tools/worktree.py create "Add fizzbuzz feature" --push`
4. **Operate Prefixed**:
   - `write_file("../worktrees/slug/module.py", code)`
   - `run_shell("git -C ../worktrees/slug status")`
5. **Commit/Push**:
   ```
   git -C ../worktrees/slug add .
   git -C ../worktrees/slug commit -m "feat(slug): description"
   git -C ../worktrees/slug push -u origin feat/slug
   ```
6. **Report**: PR link: https://github.com/rooschristopher/grok_agent/pull/new/feat/slug
7. **Cleanup** (optional): `git worktree remove ../worktrees/slug; git branch -D feat/slug`

## Exceptions (Rare):
- Explicit: "Use main branch".
- Read-only queries.
- Non-file tasks.

## Why? (Rationale)
- **Main sacred**: Never dirty production branch.
- **Parallelism**: Multiple features @ once.
- **Best Practices**: Conventional commits (`feat/`, `fix/`, etc.), isolated changes.
- **Reproducible**: Tools handle paths.

## Enforcement:
- **Injected**: agent.py loads this file → system prompt.
- **ChromaDB Retrieval**: Past examples reinforce.
- **Violate?** Self-correct via memory/tools.

Loaded automatically on EVERY run/restart/machine. Immortal! 💾