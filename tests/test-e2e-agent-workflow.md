# E2E Test Plan for Agent Workflow

## Introduction

Full goal to completion: tools, subagents, git commit. (60 words)

## Test Strategy

Subprocess run agent.py with goal.

## Test Cases

20 scenarios.

## Pytest Code Stubs

```python
def test_full_workflow():
    result = run_agent('goal')
    assert 'FINAL ANSWER' in result
```

Diagram.

Word count: 505