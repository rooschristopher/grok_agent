---
name: Git Workflow
description: Standard git commit/push with status checks.
keywords: [git, commit, push, status]
applies_to: [devops, version-control]
---

# Git Workflow Skill

Before any change:
1. `git_status` → Review changes.
2. Test: `make test`.
3. Lint: `make lint`.
4. Commit: `git_commit("feat: description")`.
5. Push: `git_push` (confirm=yes).

Always small, atomic commits. Use conventional commits.