import os
import tempfile
from pathlib import Path

import pytest

from tools.skills import parse_frontmatter


@pytest.fixture
def sample_skill_content():
    return """---
name: Test Skill
description: A test skill for TDD.
keywords: [test, yaml, parse]
applies_to: [tdd]
---
# Instructions
This is the body.
"""


def test_parse_frontmatter(sample_skill_content):
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".SKILL.md", encoding="utf-8", delete=False
    ) as f:
        f.write(sample_skill_content)
        f.flush()
        file_path = Path(f.name)

    try:
        fm = parse_frontmatter(file_path)
        assert fm is not None
        assert fm["name"] == "Test Skill"
        assert fm["description"] == "A test skill for TDD."
        assert fm["keywords"] == ["test", "yaml", "parse"]
        assert "# Instructions" in fm["full_content"]
    finally:
        os.unlink(file_path)


def test_parse_frontmatter_fallback():
    content = "# No frontmatter\\nBody"
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as f:
        f.write(content)
        f.flush()
        file_path = Path(f.name)

    try:
        fm = parse_frontmatter(file_path)
        assert fm is not None
        assert "Skill without YAML frontmatter." in fm["description"]
        assert fm["full_content"] == content.strip()
    finally:
        os.unlink(file_path)


@pytest.mark.parametrize(
    "bad_yaml",
    [
        "---\\ninvalid: yaml\\n---",
        "---bad",
        "",
    ],
)
def test_parse_invalid(bad_yaml):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(bad_yaml)
        file_path = Path(f.name)

    try:
        fm = parse_frontmatter(file_path)
        assert isinstance(fm, dict)
        assert fm["name"] != "Test Skill"  # fallback
    finally:
        os.unlink(file_path)
