import argparse
import json
import os
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.table import Table

# Assume agent.py is importable
from agent import Agent  # Hypothetical

# xAI SDK placeholders - adjust to actual
# from xai import Client
# user = ... tool_result = ...
# For now, assume defined in agent or global

console = Console()


def show_help():
    """Show slash commands help."""
    table = Table(title="🚀 Slash Commands", expand=True)
    table.add_column("Command", style="cyan")
    table.add_column("Description")
    commands = [
        ("/help", "Show this help"),
        ("/skills 🧠", "Skills dashboard"),
        ("/tools 🔧", "Tools dashboard"),
        ("/workflows 🛠️", "Workflows dashboard"),
        ("/chats", "List chat histories"),
        ("/subagents", "List subagents"),
        ("/git", "Git status"),
        ("/costs 💰", "API costs summary"),
        ("q/quit/exit", "Exit chat"),
    ]
    for cmd, desc in commands:
        table.add_row(cmd, desc)
    console.print(table)
    console.print("\n[italic]Multi-line: Enter lines, empty line to send.[/]")
    console.print("[italic]Code: Use ``` for syntax highlight.[/]")


def get_multiline_input(console):
    """Get multi-line user input."""
    lines = []
    console.print("\n[bold cyan]You[/] > ", end="")
    console.line()
    while True:
        line = input()
        if not line.strip():
            break
        lines.append(line)
    return "\n".join(lines).strip()


def skills_dashboard(agent):
    locs = ["skills", ".grok_agent/skills"]
    all_skills = []
    for loc in locs:
        try:
            js = agent.list_dir(loc)
            data = json.loads(js) if isinstance(js, str) else js
            items = data.get("items", [])
            md_files = [f for f in items if f.endswith((".md", ".SKILL.md"))]
            all_skills.extend([f"{loc}/{f}" for f in md_files])
        except Exception as e:
            console.print(f"[red]Error {loc}: {e}[/]")
    total = len(all_skills)
    console.print(f"[bold]🧠 Skills Dashboard[/bold] | Total: [magenta]{total}[/]")
    stats = Table(title="📊 Stats")
    stats.add_column("Type")
    stats.add_column("Count", justify="right")
    stats.add_row("📄 .md/.SKILL.md", str(total))
    console.print(stats)
    table = Table(title="📋 Skills", expand=True)
    table.add_column("Path", style="green")
    table.add_column("Frontmatter Preview")
    for fname in sorted(all_skills):
        preview = "[dim]-[/dim]"
        try:
            content = agent.read_file(fname)
            if content.startswith("---"):
                end_fm = content.find("\n---\n")
                if end_fm != -1:
                    fm = content[3:end_fm].strip()
                    preview = fm[:100] + "..." if len(fm) > 100 else fm
        except:
            pass
        table.add_row(fname, preview)
    console.print(table)


def tools_dashboard(agent):
    loc = "tools"
    try:
        js = agent.list_dir(loc)
        data = json.loads(js) if isinstance(js, str) else js
        items = data.get("items", [])
        py_files = [f for f in items if f.endswith(".py")]
        total = len(py_files)
        console.print(f"[bold]🔧 Tools Dashboard[/bold] | PY: [magenta]{total}[/]")
        stats = Table(title="📊 Stats")
        stats.add_column("Type")
        stats.add_column("Count", justify="right")
        stats.add_row("🐍 .py", str(total))
        console.print(stats)
        table = Table(title="📋 Tools", expand=True)
        table.add_column("Name", style="green")
        table.add_column("Preview")
        for fname in sorted(py_files):
            preview = "[dim]-[/dim]"
            try:
                content = agent.read_file(f"{loc}/{fname}")
                lines = content.splitlines()
                preview = lines[0][:80] if lines else "-"
            except:
                pass
            table.add_row(fname, preview)
        console.print(table)
    except Exception as e:
        console.print(f"[red]Error tools: {e}[/]")


def workflows_dashboard(agent):
    loc = ".grok_agent/workflows"
    try:
        wf_json = agent.list_dir(loc)
        if isinstance(wf_json, str):
            wf_data = json.loads(wf_json)
        else:
            wf_data = wf_json
        items = wf_data.get("items", [])
        md_files = [f for f in items if f.endswith(".md")]
        total = len(md_files)
        console.print(f"[bold]🛠️ Workflows Dashboard[/bold] | MD files: [magenta]{total}[/]")
        stats = Table(title="📊 Stats")
        stats.add_column("Type")
        stats.add_column("Count", justify="right")
        stats.add_row("📄 .md", str(total))
        console.print(stats)
        table = Table(title="📋 Workflows", expand=True)
        table.add_column("Name", style="green")
        table.add_column("Preview", style="white")
        for fname in sorted(md_files):
            preview = "[dim]📄[/dim]"
            try:
                content = agent.read_file(f"{loc}/{fname}")
                lines = content.splitlines()
                if lines:
                    first = lines[0].strip()
                    if first.startswith("---"):
                        end_fm = content.find("\n---\n")
                        if end_fm != -1:
                            fm = content[3:end_fm].strip()
                            preview = fm[:120] + "..." if len(fm) > 120 else fm
                        else:
                            preview = first[:120]
                    else:
                        preview = first[:120] + "..." if len(first) > 120 else first
            except:
                pass
            table.add_row(fname, preview)
        console.print(table)
    except Exception as e:
        console.print(f"[red]Error in workflows: {e}[/]")


def list_chats(target_dir):
    chats_dir = Path(target_dir) / "chats"
    if chats_dir.exists():
        chat_files = [
            f for f in chats_dir.iterdir() if f.name.startswith("chat-") and f.suffix == ".json"
        ]
        if chat_files:
            table = Table(title="📋 Recent Chats")
            table.add_column("File")
            table.add_column("Modified")
            for f in sorted(chat_files, key=lambda x: x.stat().st_mtime, reverse=True):
                mtime = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
                table.add_row(f.name, mtime)
            console.print(table)
        else:
            console.print("[yellow]No chats yet.[/]")
    else:
        console.print("[yellow]chats/ not found.[/]")


def show_subagents(agent):
    try:
        subs_json = agent.list_subagents()
        subs = json.loads(subs_json) if isinstance(subs_json, str) else subs_json
        table = Table(title="🤖 Subagents", expand=True)
        table.add_column("ID", style="cyan")
        table.add_column("Status")
        table.add_column("Goal")
        for sub in subs or []:
            goal = (
                sub.get("goal", "")[:50] + "..."
                if len(sub.get("goal", "")) > 50
                else sub.get("goal", "")
            )
            table.add_row(sub.get("agent_id", "N/A"), sub.get("status", "?"), goal)
        console.print(table)
    except Exception as e:
        console.print(f"[red]Subagents error: {e}[/]")


def get_costs_summary(path="costs.jsonl"):
    try:
        total = 0
        count = 0
        with open(path) as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    total += data.get("cost", 0)
                    count += 1
        return f"Total: ${total:.4f} | {count} calls"
    except FileNotFoundError:
        return "No costs.jsonl"
    except:
        return "Error reading costs"


def log_api_usage(model, usage):
    if not usage:
        return
    # Placeholder cost calc
    input_t = getattr(usage, "prompt_tokens", 0)
    output_t = getattr(usage, "completion_tokens", 0)
    total_t = input_t + output_t
    cost = total_t * 5e-6  # rough $ per token
    data = {"model": model, "input": input_t, "output": output_t, "total": total_t, "cost": cost}
    try:
        with open("costs.jsonl", "a") as f:
            f.write(json.dumps(data) + "\n")
    except:
        pass


def main():
    parser = argparse.ArgumentParser(description="Grok Agent Chat CLI")
    parser.add_argument("--worktree", default=".", help="Target worktree/project dir")
    parser.add_argument("--model", default="grok-beta", help="Grok model")
    parser.add_argument("--max_steps_per_turn", type=int, default=20)
    parser.add_argument("--load", help="Load chat file (future)")
    args = parser.parse_args()

    target_dir = Path(args.worktree).resolve()
    os.chdir(target_dir)
    agent = Agent(target_dir=target_dir, model=args.model)

    console.print(
        Panel(
            "🤖 Grok Chat v2.5 - Slash Commands Ready! ✨",
            title="🚀 Grok Agent",
            border_style="green",
        )
    )
    console.print(f"[bold cyan]Dir:[/] {target_dir}")
    show_help()  # Startup help

    chats_dir = target_dir / "chats"
    chats_dir.mkdir(exist_ok=True)
    session_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    chat_file = chats_dir / f"chat-{session_id}.json"
    history = []

    if chat_file.exists():
        try:
            with open(chat_file) as f:
                history = json.load(f)
            console.print(f"[green]📂 Resumed {len(history) // 2} turns from {chat_file.name}[/]")
        except:
            pass

    try:
        chat = agent.client.chat.create(model=agent.model, tools=agent.tools)
        chat.append(
            user(
                agent.system_prompt_template.format(
                    directory=str(target_dir),
                    goal="You are in interactive chat mode. Be concise & helpful.",
                )
            )
        )

        while True:
            user_input_raw = get_multiline_input(console)
            if not user_input_raw.strip():
                continue
            cmd = user_input_raw.strip().split()[0].lower() if user_input_raw.strip() else ""
            if cmd in ["quit", "exit", "q"]:
                break
            if cmd == "/help":
                show_help()
                continue
            if cmd == "/chats":
                list_chats(target_dir)
                continue
            if cmd == "/subagents":
                show_subagents(agent)
                continue
            if cmd == "/git":
                git_status = agent.run_shell("git status --short")
                console.print(Panel(git_status or "Clean", title="🌳 Git", border_style="green"))
                continue
            if cmd == "/costs":
                summary = get_costs_summary()
                console.print(Panel(summary, title="💰 Costs", border_style="yellow"))
                continue
            if cmd == "/skills":
                skills_dashboard(agent)
                continue
            if cmd == "/tools":
                tools_dashboard(agent)
                continue
            if cmd == "/workflows":
                workflows_dashboard(agent)
                continue

            # Normal message
            chat.append(user(user_input_raw))
            history.append({"role": "user", "content": user_input_raw})

            step = 1
            max_steps = args.max_steps_per_turn

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("[cyan]🤖 Thinking...", total=max_steps)
                while step <= max_steps:
                    progress.update(task, description=f"🤖 Step {step}/{max_steps}")
                    msg = chat.sample()
                    log_api_usage(agent.model, getattr(msg, "usage", None))
                    chat.append(msg)
                    history.append(
                        {
                            "role": "assistant",
                            "content": getattr(msg, "content", ""),
                            "tools_used": len(getattr(msg, "tool_calls", [])),
                        }
                    )

                    if not msg.tool_calls:
                        content = msg.content or ""
                        if "```" in content:
                            console.print(Syntax(content, "python"))
                        else:
                            console.print(Panel(Markdown(content), title="🤖", border_style="cyan"))
                        break

                    console.print(f"[green]🔧 {len(msg.tool_calls)} tools called[/]")
                    for tc in msg.tool_calls:
                        try:
                            fargs = json.loads(tc.function.arguments)
                            result = agent.tool_map[tc.function.name](**fargs)
                            preview = (
                                str(result)[:400] + "..." if len(str(result)) > 400 else str(result)
                            )
                            console.print(
                                Panel(preview, title=f"🛠️ {tc.function.name}", border_style="yellow")
                            )
                            chat.append(tool_result(result))
                        except Exception as e:
                            console.print(f"[red]Tool error: {e}[/]")
                            break
                    step += 1
                    progress.advance(task)

            # Save history
            try:
                with open(chat_file, "w") as f:
                    json.dump(history, f, indent=2)
                console.print(f"[green]💾 Saved {chat_file.name} ({len(history) // 2} turns)[/]")
            except Exception as e:
                console.print(f"[red]Save error: {e}[/]")

            # Persist to memory if available
            try:
                memory = agent.get_memory()
                if memory and history:
                    agent.memory.add_chat_messages(chat_file.stem, history[-10:])
                    console.print("[green]🧠 Synced to ChromaDB[/]")
            except:
                pass

    except KeyboardInterrupt:
        console.print("\n[bold yellow]👋 Interrupted. Chat saved![/]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/]")
    finally:
        console.print("[dim]Bye! Persistent chat in chats/[/]")


if __name__ == "__main__":
    main()
