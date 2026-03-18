---
name: TDD Cycle
description: Run full Test-Driven Development: Red → Green → Refactor.
keywords: [tdd, test, red-green-refactor, pytest]
applies_to: [coding, testing]
---

# TDD Skill Instructions

When tasked with implementing a feature:

1. **RED**: Write a failing test for the desired behavior.
   - Use pytest style.
   - Run `make test` or `pytest` to confirm FAIL.

2. **GREEN**: Write minimal code to make test PASS.
   - No refactoring yet—quickest path.

3. **REFACTOR**: Clean up code/tests while keeping tests green.
   - Run lint/format: `make lint && make format`.

Repeat for edge cases.

Tools: Use `tools/tdd.py`, `run_shell('make test')`, `git diff`.

End with committed code + docs.