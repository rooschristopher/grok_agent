import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.table import Table
from xai_sdk.chat import tool_result, user

from agent import Agent
from logger import get_logger, setup_logging

load_dotenv()
setup_logging("logs/chat.log")
logger = get_logger(__name__)

console = Console()


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
    table.add_row("/skills", "Skills dashboard 🧠")
    table.add_row("/tools", "Tools list & run 🔧")
    table.add_row("/workflows", "Workflows guides 📜")
    table.add_row("/commands", "Full slash menu 🧭")
    table.add_row("/jira", "Jira tickets dashboard 📋")
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


def parse_frontmatter(content: str) -> dict[str, Any]:
    """Parse simple YAML frontmatter."""
    if '---\n' not in content[:500]:
        return {'name': '', 'description': '', 'keywords': []}
    parts = content.split('---\n', 2)
    if len(parts) < 2:
        return {'name': '', 'description': '', 'keywords': []}
    yaml_str = parts[1]
    data = {}
    for line in yaml_str.splitlines():
        if ': ' in line:
            try:
                k, v = line.split(': ', 1)
                k = k.strip()
                v = v.strip().rstrip('.')
                if v.startswith('[') and v.endswith(']'):
                    kw_str = v[1:-1]
                    keywords = [kw.strip().strip('"\'' ) for kw in kw_str.split(',') if kw.strip()]
                    data[k] = keywords
                else:
                    data[k] = v
            except:
                pass
    return data


def skills_dashboard(agent, console: Console):
    home_dir = os.path.expanduser('~/.grok_agent/skills/')
    agent_dir = '.grok_agent/skills/'
    proj_dir = 'skills/'
    dir_info = [
        (home_dir, '🌍 Home'),
        (agent_dir, '🧠 Agent'),
        (proj_dir, '📦 Project')
    ]
    dir_stats = {}
    skills_list = []
    total = 0
    for dpath, label in dir_info:
        try:
            dir_data = json.loads(agent.list_dir(dpath))
            items = dir_data.get('items', [])
            skills = [f for f in items if f.endswith('.SKILL.md')]
            count = len(skills)
            dir_stats[label] = count
            total += count
            for f in skills:
                fpath = os.path.join(dpath.rstrip('/'), f)
                fpath_disp = fpath.replace(os.path.expanduser('~'), '~')
                cont = agent.read_file(fpath)
                fm = parse_frontmatter(cont)
                name = fm.get('name', f.replace('.SKILL.md', ''))
                desc = fm.get('description', 'No desc')[:50] + '...'
                kws = ', '.join(fm.get('keywords', [])[:4])
                skills_list.append((label[0], name, kws, desc, fpath_disp))
        except Exception:
            dir_stats[label] = 0
    console.print(f"[bold cyan]/skills - Total: {total} skills across dirs (fresh scan)[/bold]")
    if dir_stats:
        st = Table(title="📊 Stats")
        st.add_column("Dir")
        st.add_column("Count", justify="right")
        for lbl, cnt in dir_stats.items():
            st.add_row(lbl, str(cnt))
        console.print(st)
    tbl = Table(title="📋 Skills", expand=True)
    tbl.add_column("Emoji")
    tbl.add_column("Name")
    tbl.add_column("Keywords")
    tbl.add_column("Desc")
    tbl.add_column("Path")
    for em, n, kw, d, p in skills_list:
        tbl.add_row(em, n, kw, d, p)
    console.print(tbl)
    console.print("[dim]Load one? &#x27;read_file(path)&#x27; or &#x27;use skill&#x27;[/]")


def tools_dashboard(agent, console: Console):
    console.print("[bold cyan]/tools - Tools Dashboard[/bold]")
    try:
        items = json.loads(agent.list_dir("tools/"))["items"]
        py_tools = [f for f in items if f.endswith(".py") and not f.startswith("__")]
        table = Table(title="🐍 Python Tools")
        table.add_column("Name")
        table.add_column("Path")
        for f in sorted(py_tools):
            table.add_row(f[:-3], f"tools/{f}")
        console.print(table)
    except Exception as e:
        console.print(f"[yellow]Error: {e}[/]")
    console.print("[dim]Run: python tools/xxx.py --help[/]")


def workflows_dashboard(agent, console: Console):
    console.print("[bold cyan]/workflows - Workflows Dashboard[/bold]")
    console.print("[yellow]Create workflows/*.md for TDD, git-workflow etc.[/]")
    # similar impl if needed


def commands_dashboard(agent, console: Console):
    console.print("[bold cyan]/commands - Slash Commands from Instructions[/bold]")
    try:
        content = agent.read_file(".grok_agent/agent-instructions.md")
        lines = content.split("\n")
        sections = []
        i = 0
        while i < len(lines):
            if "## 🎨 /" in lines[i]:
                cmd = lines[i].split("/")[-1].split()[0]
                j = i + 1
                desc = []
                while j < len(lines) and not lines[j].startswith("##"):
                    desc.append(lines[j].strip())
                    j += 1
                sections.append( (f"/{cmd}", " ".join(desc[:2]) + "..." ) )
                i = j
            i += 1
        table = Table(title="🧭 Menu")
        table.add_column("Command")
        table.add_column("Desc")
        for c, d in sections:
            table.add_row(c, d)
        console.print(table)
    except Exception as e:
        console.print(f"[yellow]Error: {e}[/]")


def jira_dashboard(agent, console: Console):
    console.print("[bold blue]/jira - Tickets Dashboard[/bold]")
    try:
        result = agent.run_shell("python tools/jira/cli.py list-my")
        console.print(Panel(result, title="📋 My Jira Tickets", border_style="green"))
    except Exception as e:
        console.print(Panel(str(e), title="Jira Error", border_style="red"))


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

    console.print(Panel("v2.5 - Full CLI Dashboards! ✨", title="🚀", border_style="green"))
    console.print(f"[bold cyan]Worktree:[/] {target_dir}")
    show_help()  # Startup help

    chats_dir = target_dir / "chats"
    chats_dir.mkdir(exist_ok=True)
    session_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    chat_file = chats_dir / f"chat-{session_id}.json"
    history = []

    if args.load:
        load_chat(Path(args.load), chat)  # Define if needed

    if chat_file.exists():
        with open(chat_file) as f:
            history = json.load(f)
        console.print(f"[green]Resumed {len(history)} turns.[/]")

    try:
        chat = agent.client.chat.create(model=agent.model, tools=agent.tools)
        chat.append(
            user(
                agent.system_prompt_template.format(
                    directory=str(target_dir), goal="Interactive"
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
            if cmd == "/skills":
                skills_dashboard(agent, console)
                continue
            if cmd == "/tools":
                tools_dashboard(agent, console)
                continue
            if cmd == "/workflows":
                workflows_dashboard(agent, console)
                continue
            if cmd == "/commands":
                commands_dashboard(agent, console)
                continue
            if cmd == "/jira":
                jira_dashboard(agent, console)
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
                            console.print(
                                Panel(
                                    Markdown(content), title="🤖", border_style="cyan"
                                )
                            )
                        break

                    console.print(f"[green]{len(msg.tool_calls)} tools[/]")
                    for tc in msg.tool_calls:
                        fargs = json.loads(tc.function.arguments)
                        result = agent.tool_map[tc.function.name](**fargs)
                        preview = str(result)[:300] + "..."
                        console.print(
                            Panel(
                                preview, title=tc.function.name, border_style="yellow"
                            )
                        )
                        chat.append(tool_result(result))
                    step += 1

            with open(chat_file, "w") as f:
                json.dump(history, f, indent=2)
            console.print(f"[green]💾 {chat_file.name} ({len(history)} turns)[/]")

    except KeyboardInterrupt:
        console.print("\nBye!")
    finally:
        console.print("[dim]Persistent.[/]")


if __name__ == "__main__":
    main()
