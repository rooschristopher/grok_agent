import pytest
import subprocess
import json
from pathlib import Path
from agent import Agent

@pytest.fixture
def git_repo(tmp_path):
    repo_dir = tmp_path / 'repo'
    repo_dir.mkdir()
    subprocess.run(['git', 'init'], cwd=repo_dir, check=True, capture_output=True)
    file1 = repo_dir / 'file1.txt'
    file1.write_text('initial content')
    subprocess.run(['git', 'add', 'file1.txt'], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(['git', 'commit', '-m', 'initial commit'], cwd=repo_dir, check=True, capture_output=True)
    
    # Unstaged modification
    file1.write_text('modified content')
    
    # New untracked file
    (repo_dir / 'file2.txt').write_text('new content')
    
    # Staged file
    (repo_dir / 'file3.txt').write_text('staged content')
    subprocess.run(['git', 'add', 'file3.txt'], cwd=repo_dir, check=True, capture_output=True)
    
    return repo_dir

def test_git_status(git_repo):
    agent = Agent(target_dir=git_repo)
    result = agent.git_status()
    data = json.loads(result)
    expected_files = [
        {'filename': 'file1.txt', 'status': ' M'},
        {'filename': 'file2.txt', 'status': '??'},
        {'filename': 'file3.txt', 'status': 'A '},
    ]
    assert sorted(data['files'], key=lambda x: x['filename']) == sorted(expected_files, key=lambda x: x['filename'])

def test_git_status_clean(git_repo):
    # Commit all changes to make clean
    subprocess.run(['git', 'add', '.'], cwd=git_repo, check=True, capture_output=True)
    subprocess.run(['git', 'commit', '-m', 'commit changes'], cwd=git_repo, check=True, capture_output=True)
    agent = Agent(target_dir=git_repo)
    result = agent.git_status()
    data = json.loads(result)
    assert data['files'] == []

def test_git_commit(git_repo):
    agent = Agent(target_dir=git_repo)
    result = agent.git_commit('test commit')
    data = json.loads(result)
    assert data['success'] is True
    assert len(data['files']) > 0

def test_git_commit_no_changes(git_repo):
    subprocess.run(['git', 'add', '.'], cwd=git_repo, check=True)
    subprocess.run(['git', 'commit', '-m', 'all committed'], cwd=git_repo, check=True)
    agent = Agent(target_dir=git_repo)
    result = agent.git_commit('no changes')
    data = json.loads(result)
    assert data['success'] is False

def test_git_diff(git_repo):
    agent = Agent(target_dir=git_repo)
    result = agent.git_diff()
    assert len(result.strip()) > 0
    try:
        data = json.loads(result)
        assert 'error' not in data
    except:
        pass  # string diff ok

def test_git_diff_file(git_repo):
    agent = Agent(target_dir=git_repo)
    result = agent.git_diff('file1.txt')
    assert len(result.strip()) > 0 or 'file1.txt' in result

def test_git_push_confirm(git_repo):
    agent = Agent(target_dir=git_repo)
    result = agent.git_push()
    data = json.loads(result)
    assert 'confirm' in data
    assert 'Push to origin HEAD' in data['confirm']

def test_git_push_yes(git_repo):
    agent = Agent(target_dir=git_repo)
    result = agent.git_push(confirm='yes')
    data = json.loads(result)
    assert 'confirm' not in data

def test_git_pull_confirm(git_repo):
    agent = Agent(target_dir=git_repo)
    result = agent.git_pull()
    data = json.loads(result)
    assert 'confirm' in data
    assert 'Pull from origin master' in data['confirm']

def test_git_pull_yes(git_repo):
    agent = Agent(target_dir=git_repo)
    result = agent.git_pull(confirm='yes')
    data = json.loads(result)
    assert 'confirm' not in data