import os
from pathlib import Path

def test_gitignore_exists():
    assert Path('.gitignore').exists(), '.gitignore is missing'
    
def test_gitignore_content():
    gitignore = Path('.gitignore').read_text()
    required_patterns = ['.venv/', '__pycache__/', '.ruff_cache/', '.idea/', '*.log']
    for pattern in required_patterns:
        assert pattern in gitignore, f'Missing pattern: {pattern}'

def test_pyproject_toml():
    pyproject = Path('pyproject.toml').read_text()
    assert '[tool.pytest.ini_options]' in pyproject
    assert 'testpaths = [\"tests\"]' in pyproject

def test_readme_exists():
    assert Path('README.md').exists(), 'README.md is missing'

def test_readme_content():
    readme = Path('README.md').read_text()
    required = [
        '# Learning Assistant',
        'pip install -e .',
        'python agent.py',
    ]
    for text in required:
        assert text in readme, f'Missing in README: {text}'

def test_changelog():
    assert Path('CHANGELOG.md').exists()
    content = Path('CHANGELOG.md').read_text()
    assert '## [Unreleased]' in content

def test_contributing():
    assert Path('CONTRIBUTING.md').exists()
    content = Path('CONTRIBUTING.md').read_text()
    assert '# Contributing' in content
    assert 'TDD' in content
    assert 'pytest' in content