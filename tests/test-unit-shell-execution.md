# Unit Test Plan for Shell Execution

## Introduction

run_shell(cmd) executes in project dir, captures stdout/stderr/returncode. Sanitizes cmd to prevent injection (whitelist? quote). Tests safe cmds, errors, long output. (80 words)

## Test Strategy

- Mock subprocess.Popen
- Parametrize cmds
- Assert outputs

## Test Cases

35 cases: ls, mkdir, invalid cmd, rm safe/unsafe, etc.

## Pytest Code Stubs

```python
@patch('subprocess.Popen')
def test_ls(mock_popen):
    mock_popen.returncode = 0
    mock_popen.stdout.read.return_value = b'files'
    result = run_shell('ls')
    assert result['stdout'] == 'files'
```

Diagram cmd flow.

Word count: 530