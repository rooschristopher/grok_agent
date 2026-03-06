.PHONY: all test lint format clean tdd-demo install pre-commit

all: lint test format

test:
	pytest tests/ tools/ -v --tb=short

lint:
	ruff check . --fix

format:
	black .

clean:
	rm -rf __pycache__ .pytest_cache .coverage htmlcov *.egg-info

tdd-demo:
	python tools/tdd.py --spec "math.add(x, y): Returns x + y. Supports int/float. Raises ValueError for strings." --module utils.math --max-iters 5

install:
	uv sync  # Or pip install -e .

pre-commit:
	pre-commit install