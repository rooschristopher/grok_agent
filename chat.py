import argparse
import json
from pathlib import Path
import sys
import os

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.rule import Rule
from rich.text import Text
from dotenv import load_dotenv
from xai_sdk.chat import user, tool_result
from logger import setup_logging, get_logger
from agent import Agent

load_dotenv()
setup_logging("logs/app.log")
logger = get_logger(__name__)

console = Console()

def get_multiline_input(console, prompt_text="💬 You"):
    if prompt_text:
        console.print(f"[bold]{prompt_text}[/bold] (end with empty line / double Enter)")
    lines = []
    while True:
        try:
            line = console.input(" > ")
            if not line.strip():
                break
            lines.append(line)
        except (EOFError, KeyboardInterrupt):
            console.print("")
            break
    return '\n'.join(lines)

def main():
    parser = argparse.ArgumentParser(description="🚀 Interactive Chat with Grok Coding Agent")
    parser.add_argument("--target_dir", default=".", help="Target working directory")
    parser.add_argument("--model", default="grok-4-1-fast-reasoning", help="xAI model to use")
    parser.add_argument("--max_steps_per_turn", type=int, default=500, help="Max agent steps per user turn")
    args = parser.parse_args()

    target_dir = Path(args.target_dir).resolve()
    os.chdir(target_dir)
    agent = Agent(target_dir=target_dir, model=args.model)

    console.print(Panel(Text("Grok Agent Chat Ready! 💬", style="bold green"), title="🚀", border_style="green", expand=False))
    console.print(f"[dim]Working directory:[/] [bold cyan]{target_dir}[/]")
    console.print("[dim]Commands: 'quit', 'exit', 'q' to stop. End every message with double Enter (empty line). Perfect for pasting code![/]")

    try:
        chat = agent.client.chat.create(model=agent.model, tools=agent.tools)
        system_prompt = f"""You are a helpful autonomous coding agent working in this directory: {agent.target_dir}

You have access to powerful tools:
- list_dir(path): List files/directories
- read_file(filename): Read file content
- write_file(filename, content, append=False): Write/overwrite file
- run_shell(cmd): Execute shell command in project directory
- spawn_subagent(goal, max_steps=100): Spawn sub-agent for parallel task. Use list_subagents to monitor, kill_subagent if needed.
- list_subagents: Get list of all subagents and their statuses.
- kill_subagent(agent_id): Terminate a subagent by agent_id.
- web_search(query, num_results=5): Google search

CRITICAL FORMATTING RULES:
- Use actual newlines in code blocks (```python
code here
```). Do NOT use literal \\n in displayed code.
- Do NOT use HTML entities like &quot;, &lt;, &gt;. Use " < > directly.
- For tool parameters like write_file's content (JSON string), use \\n to represent newlines in multi-line strings.

Think step-by-step. Use tools when needed to assist the user.
For complex tasks, spawn subagents.
Be concise, helpful, and use FINAL ANSWER when completing a goal."""
        chat.append(user(system_prompt))

        while True:
            user_input_raw = get_multiline_input(console)
            user_input_stripped = user_input_raw.strip()
            if not user_input_stripped:
                continue
            if user_input_stripped.lower() in ['quit', 'exit', 'q']:
                console.print("[bold yellow]👋 Bye![/]")
                break

            chat.append(user(user_input_raw))
            step = 1
            max_steps = args.max_steps_per_turn

            while step <= max_steps:
                console.print(Rule(title=f"🤖 Agent Turn Step {step}/{max_steps}", style="bright_blue"))

                try:
                    msg = chat.sample()
                except Exception as e:
                    console.print(f"[red]❌ Sample error: {str(e)}[/]")
                    logger.error("Sample error: %s", e)
                    break

                chat.append(msg)

                if not hasattr(msg, 'tool_calls') or not msg.tool_calls:
                    content = getattr(msg, 'content', 'No response')
                    console.print(Panel(Markdown(content), title="🤖 Agent", border_style="cyan"))
                    break

                console.print(f"[bold green]🔧 {len(msg.tool_calls)} tool call(s)[/]")

                for i, tc in enumerate(msg.tool_calls, 1):
                    fname = getattr(tc.function, 'name', 'unknown')
                    try:
                        fargs_str = tc.function.arguments
                        fargs = json.loads(fargs_str) if isinstance(fargs_str, str) else {}
                    except json.JSONDecodeError:
                        fargs = {}
                        logger.warning("Invalid tool args: %s", fargs_str)

                    console.print(f"  [green]{i}. [bold]{fname}[/bold]({fargs})[/]")

                    try:
                        handler = agent.tool_map.get(fname)
                        if handler:
                            result = handler(**fargs)
                        else:
                            result = json.dumps({"error": f"Unknown tool: {fname}"})
                    except Exception as e:
                        logger.exception("Tool %s failed", fname)
                        result = json.dumps({"error": str(e)})

                    try:
                        res_data = json.loads(result)
                        preview = json.dumps(res_data, indent=2)[:400]
                        if len(json.dumps(res_data)) > 400:
                            preview += "..."
                    except:
                        preview = str(result)[:400] + "..." if len(str(result)) > 400 else str(result)

                    console.print(Panel(f"[yellow]{preview}[/]", title="📄 Result", border_style="yellow"))
                    chat.append(tool_result(result))

                step += 1

            if step > max_steps:
                console.print("[orange1]⚠️ Max steps per turn reached. Send next message or adjust --max_steps_per_turn.[/]")

    except KeyboardInterrupt:
        console.print("\n[red]⏹️ Interrupted by user.[/]")
    except Exception as e:
        console.print(f"[red]❌ Fatal error: {e}[/]")
        logger.exception("Chat fatal error")
    finally:
        console.print("[dim]Cleaning up...[/]")
        # Agent cleanup via atexit

if __name__ == "__main__":
    main()
