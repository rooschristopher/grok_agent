import pytest
import json
from pathlib import Path
from agent import Agent
import subprocess

@pytest.fixture
def agent(tmp_path):
    return Agent(target_dir=tmp_path)

def test_list_dir_empty(agent, tmp_path):
    result = agent.list_dir(str(tmp_path))
    data = json.loads(result)
    assert data['path'] == str(tmp_path)
    assert data['items'] == []

def test_list_dir_dot(agent, tmp_path):
    result = agent.list_dir(".")
    data = json.loads(result)
    assert data['path'] == "."
    assert data['items'] == []

def test_list_dir_with_files(agent, tmp_path):
    (tmp_path / 'file1.txt').touch()
    result = agent.list_dir(str(tmp_path))
    data = json.loads(result)
    assert data['path'] == str(tmp_path)
    assert 'file1.txt' in data['items']

def test_list_dir_error(agent, tmp_path):
    bad_path = str(tmp_path / "nonexistent")
    result = agent.list_dir(bad_path)
    data = json.loads(result)
    assert 'error' in data

def test_read_file_exists(agent, tmp_path):
    (tmp_path / 'test.txt').write_text('hello')
    result = agent.read_file('test.txt')
    assert result == 'hello'

def test_read_file_not_exists(agent, tmp_path):
    result = agent.read_file('nope.txt')
    data = json.loads(result)
    assert data['error'] == 'Not a file'

def test_read_file_directory(agent, tmp_path):
    (tmp_path / 'mydir').mkdir()
    result = agent.read_file('mydir')
    data = json.loads(result)
    assert data['error'] == 'Not a file'

def test_read_file_unicode(agent, tmp_path):
    content = "hello\\nworld\\u2603"
    (tmp_path / 'unicode.txt').write_text(content)
    result = agent.read_file('unicode.txt')
    assert result == content

def test_read_file_invalid_utf8(agent, tmp_path):
    (tmp_path / 'invalid.txt').write_bytes(b'hello \\xff\\xfe world')
    result = agent.read_file('invalid.txt')
    assert result.startswith('hello ')
    assert 'world' in result

def test_write_file_overwrite(agent, tmp_path):
    result = agent.write_file('overwrite.txt', 'new content')
    data = json.loads(result)
    assert data['status'] == 'ok'
    assert (tmp_path / 'overwrite.txt').read_text() == 'new content'

def test_write_file_append_new(agent, tmp_path):
    result = agent.write_file('append_new.txt', 'content', append=True)
    data = json.loads(result)
    assert data['status'] == 'ok'
    assert (tmp_path / 'append_new.txt').read_text() == 'content'

def test_write_file_append_existing(agent, tmp_path):
    (tmp_path / 'exist.txt').write_text('original')
    result = agent.write_file('exist.txt', ' append', append=True)
    data = json.loads(result)
    assert data['status'] == 'ok'
    assert (tmp_path / 'exist.txt').read_text() == 'original append'

def test_write_file_unicode(agent, tmp_path):
    content = "caf\\xe9\\n\\u2603"
    result = agent.write_file('unicode.txt', content)
    data = json.loads(result)
    assert data['status'] == 'ok'
    assert (tmp_path / 'unicode.txt').read_text() == content

def test_write_file_error_no_parent(agent, tmp_path):
    result = agent.write_file('subdir/missing.txt', 'content')
    data = json.loads(result)
    assert 'error' in data

def test_run_shell_success(agent, monkeypatch):
    def mock_run(cmd, **kwargs):
        class MockResult:
            stdout = 'mock stdout'
            stderr = 'mock stderr'
            returncode = 0
        return MockResult()
    monkeypatch.setattr('subprocess.run', mock_run)
    result = agent.run_shell('mock cmd')
    data = json.loads(result)
    assert data['stdout'] == 'mock stdout'
    assert data['stderr'] == 'mock stderr'
    assert data['returncode'] == 0

def test_run_shell_nonzero(agent, monkeypatch):
    def mock_run(cmd, **kwargs):
        class MockResult:
            stdout = ''
            stderr = 'error msg'
            returncode = 1
        return MockResult()
    monkeypatch.setattr('subprocess.run', mock_run)
    result = agent.run_shell('fail')
    data = json.loads(result)
    assert data['returncode'] == 1
    assert data['stderr'] == 'error msg'

def test_run_shell_exception(agent, monkeypatch):
    def mock_run(cmd, **kwargs):
        raise Exception('mock exception')
    monkeypatch.setattr('subprocess.run', mock_run)
    result = agent.run_shell('timeout')
    data = json.loads(result)
    assert 'error' in data
    assert 'mock exception' in data['error']

def test_run_shell_echo(agent, tmp_path):
    result = agent.run_shell('echo hello')
    data = json.loads(result)
    assert data['returncode'] == 0
    assert data['stdout'] == 'hello'
    assert data['stderr'] == ''

def test_run_shell_false(agent, tmp_path):
    result = agent.run_shell('false')
    data = json.loads(result)
    assert data['returncode'] == 1
    assert data['stdout'] == ''
    assert data['stderr'] == ''