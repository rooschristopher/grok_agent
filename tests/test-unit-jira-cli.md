# Unit Test Plan for Jira CLI

## Introduction

jira_list_my_tickets etc, parse JSON to MD dashboard with stats, emojis, tables. (70 words)

## Test Strategy

Mock JSON input.

## Test Cases

30 cases for formats, empty, errors.

## Pytest Code Stubs

```python
def test_format_table(json_tickets):
    md = format_jira_table(json_tickets)
    assert '🔄 In Progress' in md
```

Diagram table gen.

Word count: 525