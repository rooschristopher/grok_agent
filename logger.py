import json
import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

_initialized = False

_LEVEL_ALIASES = {
    "CRITICAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "WARN": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
    "NOTSET": logging.NOTSET,
}


def _coerce_level(level: object | None) -> int:
    if level is None:
        # Env overrides
        env = os.getenv("LOG_LEVEL") or os.getenv("APP_LOG_LEVEL")
        if env:
            level = env
        else:
            return logging.INFO
    if isinstance(level, int):
        return level
    try:
        if isinstance(level, str):
            return _LEVEL_ALIASES.get(level.strip().upper(), logging.INFO)
    except Exception:
        pass
    return logging.INFO


def setup_logging(log_path: str = "logs/app.log", level: object | None = None) -> None:
    """
    Idempotent logging setup with a rotating file handler.

    - log_path: path to the log file (created in project root by default)
    - level: logging level or string (DEBUG/INFO/...). If None, reads LOG_LEVEL/APP_LOG_LEVEL.
    """
    global _initialized
    if _initialized:
        return

    os.makedirs(os.path.dirname(log_path) or ".", exist_ok=True)

    root = logging.getLogger()
    root.setLevel(_coerce_level(level))

    # Avoid duplicate handlers if setup is called more than once
    has_file = any(isinstance(h, RotatingFileHandler) for h in root.handlers)
    if not has_file:
        file_handler = RotatingFileHandler(
            log_path, maxBytes=10 * 1024 * 1024, backupCount=10, encoding="utf-8"
        )
        fmt = logging.Formatter(
            fmt="%(asctime)s.%(msecs)03d [%(levelname)s] %(name)s:%(lineno)d %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(fmt)
        file_handler.setLevel(_coerce_level(level))
        root.addHandler(file_handler)

    # Also ensure a console handler exists only once (INFO by default)
    try:
        from rich.logging import RichHandler

        has_console = any(isinstance(h, RichHandler) for h in root.handlers)
    except ImportError:
        RichHandler = None
        has_console = any(
            isinstance(h, logging.StreamHandler) and not isinstance(h, RotatingFileHandler)
            for h in root.handlers
        )

    if not has_console:
        if "RichHandler" in locals():
            ch = RichHandler(show_level=True, show_path=True, show_time=True)
            ch.setLevel(logging.INFO)
        else:
            ch = logging.StreamHandler()
            ch.setLevel(_coerce_level(level))
            ch.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        root.addHandler(ch)

    _initialized = True


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a module-scoped logger."""
    return logging.getLogger(name or __name__)


COSTS_FILE = "costs.jsonl"
INPUT_COST_PER_M = 5.0  # USD per million input tokens for grok-beta
OUTPUT_COST_PER_M = 15.0  # USD per million output tokens
INPUT_COST_PER_TOKEN = INPUT_COST_PER_M / 1_000_000
OUTPUT_COST_PER_TOKEN = OUTPUT_COST_PER_M / 1_000_000


def log_api_usage(model: str, usage) -> None:
    """Log Grok API usage and estimated cost to costs.jsonl"""
    if not hasattr(usage, "prompt_tokens") or usage.prompt_tokens is None:
        return  # Skip if no usage info

    prompt_tokens = getattr(usage, "prompt_tokens", 0)
    completion_tokens = getattr(usage, "completion_tokens", 0)
    total_tokens = getattr(usage, "total_tokens", 0)
    reasoning_tokens = getattr(usage, "reasoning_tokens", 0)

    input_cost = INPUT_COST_PER_TOKEN * prompt_tokens
    output_cost = OUTPUT_COST_PER_TOKEN * completion_tokens
    total_cost = input_cost + output_cost

    entry = {
        "timestamp": datetime.now().isoformat(),
        "model": model,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "reasoning_tokens": reasoning_tokens,
        "input_cost": input_cost,
        "output_cost": output_cost,
        "total_cost": total_cost,
    }

    os.makedirs(os.path.dirname(COSTS_FILE) or ".", exist_ok=True)
    with open(COSTS_FILE, "a", encoding="utf-8") as f:
        json.dump(entry, f)
        f.write("\n")


def get_costs_summary() -> str:
    """Get formatted summary of API costs from costs.jsonl"""
    if not os.path.exists(COSTS_FILE):
        return "No API costs logged yet. Run some chats/agents to track!"

    data = []
    total_prompt = total_completion = total_reasoning = total_cost = 0
    n_calls = 0

    try:
        with open(COSTS_FILE, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                entry = json.loads(line)
                data.append(entry)
                total_prompt += entry["prompt_tokens"]
                total_completion += entry["completion_tokens"]
                total_reasoning += entry.get("reasoning_tokens", 0)
                total_cost += entry["total_cost"]
                n_calls += 1
    except Exception:
        return "Error reading costs.jsonl"

    if n_calls == 0:
        return "No valid entries in costs.jsonl"

    avg_cost = total_cost / n_calls

    summary = f"""📊 **API Cost Summary**
• Total calls: {n_calls}
• Total prompt tokens: {total_prompt:,}
• Total completion tokens: {total_completion:,}
• Total reasoning tokens: {total_reasoning:,}
• **Total estimated cost: ${total_cost:.6f}**
• Avg cost per call: ${avg_cost:.6f}

💡 Pricing: Input ${INPUT_COST_PER_M}/M tokens, Output ${OUTPUT_COST_PER_M}/M tokens (grok-beta rates)
"""
    return summary
