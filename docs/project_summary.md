# Learning Assistant Project Summary

The **Learning_Assistant** is an open-source Python framework designed for building and running autonomous AI coding agents powered by the xAI Grok API (specifically models like grok-4-1-fast-reasoning).

## Core Functionality
- **Autonomous Agents**: Agents can achieve goals by reasoning step-by-step, using tools to interact with the local filesystem and execute shell commands.
- **Tools Provided**:
  - `list_dir`: List files and directories.
  - `read_file`: Read file contents.
  - `write_file`: Write or append to files.
  - `run_shell`: Execute shell commands.
- **Self-Referential**: The agent can analyze, summarize, and even modify its own codebase.

## Key Files and Components
- **learning.py**: Main standalone agent implementation using xAI SDK. Runs a loop processing tool calls until a final answer.
- **agents/base.py**: Base class for generic agents that integrate LLMs with custom tools.
- **tools/**:
  - `base.py`: Abstract base for tools.
  - `weather.py`: Example tool (weather lookup).
- **voice.py**: Voice mode using xAI Realtime API for real-time voice conversations (push-to-talk with Ctrl+Enter).
- **logger.py**: Configurable logging with file rotation and console output.
- **docs/**: Documentation, including this summary and README.md.
- Other: `.env` for API keys, `.venv`, Git repo, etc.

## Usage
- Set `XAI_API_KEY` in `.env`.
- Run `python agent.py` to demo with a goal (self-summarizes).
- Run `python voice.py` for voice interaction.
- Extend by adding custom agents/tools.

## Purpose
This project serves as a learning tool and demo for tool-using AI agents, emphasizing modularity and real-world interactions like voice and code editing.

This summary was generated autonomously by the agent itself.