import argparse
import json
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.table import Table
from xai_sdk.chat import tool_result, user

from agent import Agent
from logger import get_costs_summary, get_logger, log_api_usage, setup_logging

load_dotenv()
setup_logging("logs/chat.log")
logger = get_logger(__name__)

console = Console()


def get_desc(agent, path: str) -> str:
    try:
        content = agent.read_file(path)
        lines = [line.strip() for line in content.splitlines()[:20]]
        for line in lines:
            if line.startswith("# "):
                desc = line[2:]
                return desc[:120] + "..." if len(desc) > 120 else desc
        if lines:
            desc = lines[0]
            return desc[:120] + "..." if len(desc) > 120 else desc
        return Path(path).stem
    except Exception:
        return "Unable to read"


def skills_dashboard(agent):
    dirs = ["skills", ".grok_agent/skills"]
    skills_list = []
    dir_counts = dict.fromkeys(dirs, 0)
    for d in dirs:
        try:
            listing = agent.list_dir(d)
            items = listing.get("items", [])
            for item in items:
                if item.lower().endswith(".md"):
                    pstr = f"{d}/{item}"
                    desc = get_desc(agent, pstr)
                    try:
                        ts = os.path.getmtime(pstr)
                    except OSError:
                        ts = 0
                    mtime = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
                    skills_list.append(
                        {
                            "name": item,
                            "path": pstr,
                            "desc": desc,
                            "updated": mtime,
                            "timestamp": ts,
                        }
                    )
                    dir_counts[d] += 1
        except Exception:
            pass
    total = len(skills_list)
    # Stats
    stats_table = Table.grid(expand=True, padding=(0, 1))
    stats_table.add_column("📊", style="bold magenta", no_wrap=True)
    stats_table.add_column("Count", justify="right", style="cyan")
    stats_table.add_row("Total", str(total))
    for dname, cnt in dir_counts.items():
        if cnt > 0:
            stats_table.add_row(f"📁 {Path(dname).name}", str(cnt))
    console.print(Panel(stats_table, title="🧠 Skills Stats", border_style="blue"))
    # Main table
    skills_list.sort(key=lambda x: x["timestamp"], reverse=True)
    table = Table(title=f"Skills Dashboard ({total} items, updated desc)", header_style="bold cyan")
    table.add_column(" ", no_wrap=True)
    table.add_column("Name", style="cyan")
    table.add_column("Updated", style="green")
    table.add_column("Path")
    table.add_column("Description", ratio=2)
    for s in skills_list:
        emoji = "🧠" if ".SKILL" in s["name"].upper() else "📄"
        table.add_row(emoji, s["name"], s["updated"], s["path"], s["desc"])
    console.print(table)


def tools_dashboard(agent):
    dirs = ["tools", ".grok_agent/tools"]
    tools_list = []
    dir_counts = dict.fromkeys(dirs, 0)
    for d in dirs:
        try:
            listing = agent.list_dir(d)
            items = listing.get("items", [])
            for item in items:
                if item.endswith(".py"):
                    pstr = f"{d}/{item}"
                    desc = get_desc(agent, pstr)
                    try:
                        ts = os.path.getmtime(pstr)
                    except OSError:
                        ts = 0
                    mtime = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
                    tools_list.append(
                        {
                            "name": item,
                            "path": pstr,
                            "desc": desc,
                            "updated": mtime,
                            "timestamp": ts,
                        }
                    )
                    dir_counts[d] += 1
        except Exception:
            pass
    total = len(tools_list)
    # Stats
    stats_table = Table.grid(expand=True, padding=(0, 1))
    stats_table.add_column("📊", style="bold magenta", no_wrap=True)
    stats_table.add_column("Count", justify="right", style="cyan")
    stats_table.add_row("Total", str(total))
    for dname, cnt in dir_counts.items():
        if cnt > 0:
            stats_table.add_row(f"📁 {Path(dname).name}", str(cnt))
    console.print(Panel(stats_table, title="🔧 Tools Stats", border_style="green"))
    # Main table
    tools_list.sort(key=lambda x: x["timestamp"], reverse=True)
    table = Table(title=f"Tools Dashboard ({total} items, updated desc)", header_style="bold cyan")
    table.add_column(" ", no_wrap=True)
    table.add_column("Name", style="cyan")
    table.add_column("Updated", style="green")
    table.add_column("Path")
    table.add_column("Description", ratio=2)
    for t in tools_list:
        emoji = "🔧"
        table.add_row(emoji, t["name"], t["updated"], t["path"], t["desc"])
    console.print(table)


def workflows_dashboard(agent):
    dirs = [".grok_agent/workflows", "skills", "."]
    workflows_list = []
    dir_counts = dict.fromkeys(dirs, 0)
    for d in dirs:
        try:
            listing = agent.list_dir(d)
            items = listing.get("items", [])
            for item in items:
                if item.endswith(".md") and "readme" not in item.lower():
                    pstr = item if d == "." else f"{d}/{item}"
                    desc = get_desc(agent, pstr)
                    try:
                        ts = os.path.getmtime(pstr)
                    except OSError:
                        ts = 0
                    mtime = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
                    workflows_list.append(
                        {
                            "name": item,
                            "path": pstr,
                            "desc": desc,
                            "updated": mtime,
                            "timestamp": ts,
                        }
                    )
                    dir_counts[d] += 1
        except Exception:
            pass
    total = len(workflows_list)
    # Stats
    stats_table = Table.grid(expand=True, padding=(0, 1))
    stats_table.add_column("📊", style="bold magenta", no_wrap=True)
    stats_table.add_column("Count", justify="right", style="cyan")
    stats_table.add_row("Total", str(total))
    for dname, cnt in dir_counts.items():
        if cnt > 0:
            stats_table.add_row(f"📁 {Path(dname).name}", str(cnt))
    console.print(Panel(stats_table, title="🛠️ Workflows Stats", border_style="yellow"))
    # Main table
    workflows_list.sort(key=lambda x: x["timestamp"], reverse=True)
    table = Table(
        title=f"Workflows Dashboard ({total} items, updated desc)", header_style="bold cyan"
    )
    table.add_column(" ", no_wrap=True)
    table.add_column("Name", style="cyan")
    table.add_column("Updated", style="green")
    table.add_column("Path")
    table.add_column("Description", ratio=2)
    for w in workflows_list:
        emoji = "🛠️"
        table.add_row(emoji, w["name"], w["updated"], w["path"], w["desc"])
    console.print(table)


def get_multiline_input(console):
    console.print("[bold]💬 You (empty line to send)[/bold]")
    lines = []
    while True:
        line = console.input(" > ")
        if not line.strip():
            break
        lines.append(line)
    return "\\n".join(lines)


def show_help():
    table = Table(title="🆘 Commands")
    table.add_column("Command", style="cyan")
    table.add_column("Description")
    table.add_row("/help", "Show this help")
    table.add_row("/chats", "List sessions w/ summaries")
    table.add_row("/subagents", "Live subagents table")
    table.add_row("/git", "Git status")
    table.add_row("/costs", "API costs summary")
    table.add_row("/skills 🧠", "Skills dashboard")
    table.add_row("/tools 🔧", "Tools list & run")
    table.add_row("/workflows 🛠️", "Workflows guides")
    table.add_row("quit/q/exit", "Stop chat")
    table.add_row("", "Multi-line: Paste code, end w/ empty line")
    table.add_row("--load FILE", "Resume session")
    console.print(table)
    console.print("[dim]Type message or /cmd...[/]")


def show_subagents(agent):
    subs_json = agent.list_subagents()
    try:
        subs = json.loads(subs_json).get("subagents", [])
    except:
        subs = []
    table = Table(title="🕷️ Subagents")
    table.add_column("ID")
    table.add_column("Status")
    table.add_column("Goal")
    for sub in subs:
        table.add_row(
            sub.get("agent_id", "N/A"),
            sub.get("status", "unknown"),
            sub.get("goal", "")[:50],
        )
    console.print(table)


def list_chats(target_dir):
    chats_dir = target_dir / "chats"
    if not chats_dir.exists():
        console.print("[yellow]No chats.[/]")
        return
    chats = []
    for f in chats_dir.glob("chat-*.json"):
        try:
            with open(f) as fd:
                data = json.load(fd)
            turns = len(data)
            first = data[0].get("content", "")[:50] + "..." if data else ""
            last = data[-1].get("content", "")[:50] + "..." if data else ""
            summary = f"{turns} turns | First: {first} | Last: {last}"
            chats.append((f.name, turns, summary))
        except:
            chats.append((f.name, 0, "Corrupt"))
    table = Table(title="📚 Chats")
    table.add_column("File")
    table.add_column("Turns")
    table.add_column("Summary")
    for name, turns, sumy in sorted(chats, key=lambda x: x[1], reverse=True):
        table.add_row(name, str(turns), sumy)
    console.print(table)


def main():
    parser = argparse.ArgumentParser(description="Grok Chat v2.5")
    parser.add_argument("--worktree", default=".", help="Worktree dir")
    parser.add_argument("--model", default="grok-4-1-fast-reasoning")
    parser.add_argument("--max_steps_per_turn", type=int, default=20)
    parser.add_argument("--load", help="Load chat file")
    args = parser.parse_args()

    target_dir = Path(args.worktree).resolve()
    os.chdir(target_dir)
    agent = Agent(target_dir=target_dir, model=args.model)

    console.print(Panel("v2.5 - /help + Full UI! ✨", title="🚀", border_style="green"))
    console.print(f"[bold cyan]Worktree:[/] {target_dir}")
    show_help()  # Startup help

    chats_dir = target_dir / "chats"
    chats_dir.mkdir(exist_ok=True)
    session_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    chat_file = chats_dir / f"chat-{session_id}.json"
    history = []

    # if args.load:
    #     load_chat(Path(args.load), chat)  # Define if needed

    if chat_file.exists():
        with open(chat_file) as f:
            history = json.load(f)
        console.print(f"[green]Resumed {len(history)} turns.[/]")

    try:
        chat = agent.client.chat.create(model=agent.model, tools=agent.tools)
        chat.append(
            user(
                agent.system_prompt_template.format(
                    directory=str(target_dir), goal="Interactive chat. Be helpful."
                )
            )
        )

        while True:
            user_input_raw = get_multiline_input(console)
            if not user_input_raw.strip():
                continue
            cmd = user_input_raw.strip().split()[0].lower()
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
                console.print(Panel(git_status, title="Git"))
                continue
            if cmd == "/costs":
                summary = get_costs_summary()
                console.print(Panel(summary, title="💰 API Costs", border_style="green"))
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

            chat.append(user(user_input_raw))
            history.append({"role": "user", "content": user_input_raw})

            step = 1
            max_steps = args.max_steps_per_turn

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("[cyan]🤖", total=max_steps)
                while step <= max_steps:
                    progress.update(task, description=f"Step {step}")
                    msg = chat.sample()
                    log_api_usage(agent.model, getattr(msg, "usage", None))
                    chat.append(msg)
                    history.append(
                        {
                            "role": "assistant",
                            "content": getattr(msg, "content", ""),
                            "tools": len(getattr(msg, "tool_calls", [])),
                        }
                    )

                    if not msg.tool_calls:
                        content = msg.content
                        if "```" in content:
                            console.print(Syntax(content, "markdown"))
                        else:
                            console.print(Panel(Markdown(content), title="🤖", border_style="cyan"))
                        break

                    console.print(f"[green]{len(msg.tool_calls)} tools[/]")
                    for tc in msg.tool_calls:
                        fargs = json.loads(tc.function.arguments)
                        result = agent.tool_map[tc.function.name](**fargs)
                        preview = str(result)[:300] + "..."
                        console.print(Panel(preview, title=tc.function.name, border_style="yellow"))
                        chat.append(tool_result(result))
                    step += 1

            with open(chat_file, "w") as f:
                json.dump(history, f, indent=2)
            console.print(f"[green]💾 {chat_file.name} ({len(history)} turns)[/]")

            # Persist to ChromaDB
            memory = agent.get_memory()
            if memory:
                agent.memory.add_chat_messages(chat_file.stem, history[-10:])
                console.print("[green]🧠 Persisted recent chat to ChromaDB[/]")

    except KeyboardInterrupt:
        console.print("\nBye!")
    finally:
        console.print("[dim]Persistent.[/]")


if __name__ == "__main__":
    main()
