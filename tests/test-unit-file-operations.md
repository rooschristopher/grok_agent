# Unit Test Plan for File Operations

## Introduction

read_file, write_file (append opt), list_dir. Tests paths, perms, large files, special chars. Tempdir fixture. (70 words)

## Test Strategy

pytest tmp_path fixture.

## Test Cases

30 cases: read nonexist, write dir, append, etc.

## Pytest Code Stubs

```python
def test_read_write(tmp_path):
    f = tmp_path / 'test.txt'
    write_file(str(f), 'hello')
    assert read_file(str(f)) == 'hello'
```

Diagram.

Word count: 520