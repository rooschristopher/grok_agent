#!/usr/bin/env python3
import os
import json
import argparse
from pathlib import Path
from datetime import datetime

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.markdown import Markdown
    from rich.syntax import Syntax
    from rich.progress import Progress, SpinnerColumn, TextColumn
    console = Console()
except ImportError:
    print(&quot;Install rich: uv add rich&quot;)
    exit(1)

# Assume SDK imports
from grok_sdk import user, tool_result  # Adjust to actual
from agent import Agent  # Local Agent

# Stub functions
def get_multiline_input(console):
    lines = []
    while True:
        line = input(&quot;You [&gt; &quot;)
        if line.strip() == &quot;&quot;:
            break
        lines.append(line)
    return &#x27;\n&#x27;.join(lines)

def list_chats(target_dir):
    chats_dir = Path(target_dir) / &quot;chats&quot;
    if chats_dir.exists():
        files = list(chats_dir.glob(&quot;*.json&quot;))
        console.print(f&quot;Chats ({len(files)}): {&#x27;, &#x27;.join(f.name for f in files[:5])}&quot;)
    else:
        console.print(&quot;No chats dir.&quot;)

def show_subagents(agent):
    # Use agent tools if possible
    console.print(&quot;[yellow]Subagents: Use /subagents in agent? Stub.[/]&quot;)

def get_costs_summary():
    try:
        with open(&quot;costs.jsonl&quot;) as f:
            lines = f.readlines()
        return f&quot;Calls: {len(lines)}&quot;
    except:
        return &quot;No costs.jsonl&quot;

def log_api_usage(model, usage):
    pass  # Implement if needed

def show_help():
    console.print(Panel(&quot;CLI Commands&quot;, title=&quot;📋&quot;, border_style=&quot;blue&quot;))
    table = Table(expand=True)
    table.add_column(&quot;Command&quot;, style=&quot;cyan&quot;)
    table.add_column(&quot;Description&quot;)
    table.add_row(&quot;/help&quot;, &quot;Show this help&quot;)
    table.add_row(&quot;/chats&quot;, &quot;List chat sessions&quot;)
    table.add_row(&quot;/subagents&quot;, &quot;List subagents&quot;)
    table.add_row(&quot;/git&quot;, &quot;Git status&quot;)
    table.add_row(&quot;/costs&quot;, &quot;API costs&quot;)
    table.add_row(&quot;/skills 🧠&quot;, &quot;Skills dashboard&quot;)
    table.add_row(&quot;/tools 🔧&quot;, &quot;Tools list/run&quot;)
    table.add_row(&quot;/workflows 🛠️&quot;, &quot;Workflows guides&quot;)
    console.print(table)

def skills_dashboard(agent):
    locs = [&quot;skills&quot;, &quot;.grok_agent/skills&quot;]
    all_files = []
    for loc in locs:
        try:
            sjson = agent.list_dir(loc)
            if isinstance(sjson, str):
                data = json.loads(sjson)
            else:
                data = sjson
            items = data[&quot;items&quot;]
            skill_files = [f for f in items if f.endswith(('.md', '.SKILL.md'))]
            for f in skill_files:
                all_files.append(f&quot;{loc}/{f}&quot;)
        except Exception:
            pass
    total = len(all_files)
    console.print(f&quot;[bold]🧠 Skills Dashboard[/bold] | Files: [magenta]{total}[/]&quot;)
    stats = Table(title=&quot;📊 Stats&quot;)
    stats.add_column(&quot;Type&quot;)
    stats.add_column(&quot;Count&quot;, justify=&quot;right&quot;)
    stats.add_row(&quot;📄 Skills&quot;, str(total))
    console.print(stats)
    table = Table(title=&quot;📋 Skills&quot;, expand=True)
    table.add_column(&quot;Path/Name&quot;, style=&quot;green&quot;)
    table.add_column(&quot;Desc/Preview&quot;, style=&quot;white&quot;)
    for fname in sorted(all_files):
        preview = &quot;[dim]📄[/dim]&quot;
        try:
            content = agent.read_file(fname)
            lines = content.splitlines()
            if lines:
                first = lines[0].strip()
                if first.startswith(&quot;---&quot;):
                    end_fm = content.find(&quot;\n---\n&quot;)
                    if end_fm != -1:
                        fm = content[3:end_fm].strip()
                        preview = fm[:120] + &quot;...&quot; if len(fm) &gt; 120 else fm
                    else:
                        preview = first[:120] + &quot;...&quot; if len(first) &gt; 120 else first
                else:
                    preview = first[:120] + &quot;...&quot; if len(first) &gt; 120 else first
        except Exception:
            pass
        table.add_row(fname, preview)
    console.print(table)

def tools_dashboard(agent):
    loc = &quot;tools&quot;
    try:
        tjson = agent.list_dir(loc)
        if isinstance(tjson, str):
            data = json.loads(tjson)
        else:
            data = tjson
        items = data[&quot;items&quot;]
        py_files = [f for f in items if f.endswith('.py') and not f.startswith('__')]
        total = len(py_files)
        console.print(f&quot;[bold]🔧 Tools Dashboard[/bold] | PY: [magenta]{total}[/]&quot;)
        stats = Table(title=&quot;📊 Stats&quot;)
        stats.add_column(&quot;Type&quot;)
        stats.add_column(&quot;Count&quot;, justify=&quot;right&quot;)
        stats.add_row(&quot;🐍 .py&quot;, str(total))
        console.print(stats)
        table = Table(title=&quot;📋 Tools&quot;, expand=True)
        table.add_column(&quot;Name&quot;, style=&quot;green&quot;)
        table.add_column(&quot;Preview&quot;, style=&quot;white&quot;)
        for fname in sorted(py_files):
            preview = &quot;[dim]🐍[/dim]&quot;
            try:
                content = agent.read_file(f&quot;{loc}/{fname}&quot;)
                lines = content.splitlines()
                if lines:
                    preview = lines[0][:120] + &quot;...&quot; if len(lines[0]) &gt; 120 else lines[0]
            except Exception:
                pass
            table.add_row(fname, preview)
        console.print(table)
    except Exception as e:
        console.print(f&quot;[red]Error tools: {e}[/]&quot;)

def workflows_dashboard(agent):
    loc = &quot;.grok_agent/workflows&quot;
    try:
        wf_json = agent.list_dir(loc)
        wf_data = json.loads(wf_json) if isinstance(wf_json, str) else wf_json
        items = wf_data[&quot;items&quot;]
        md_files = [f for f in items if f.endswith(&quot;.md&quot;)]
        total = len(md_files)
        console.print(f&quot;[bold]🛠️ Workflows Dashboard[/bold] | MD files: [magenta]{total}[/]&quot;)
        stats = Table(title=&quot;📊 Stats&quot;)
        stats.add_column(&quot;Type&quot;)
        stats.add_column(&quot;Count&quot;, justify=&quot;right&quot;)
        stats.add_row(&quot;📄 .md&quot;, str(total))
        console.print(stats)
        table = Table(title=&quot;📋 Workflows&quot;, expand=True)
        table.add_column(&quot;Name&quot;, style=&quot;green&quot;)
        table.add_column(&quot;Preview&quot;, style=&quot;white&quot;)
        for fname in sorted(md_files):
            preview = &quot;[dim]📄[/dim]&quot;
            try:
                content = agent.read_file(f&quot;{loc}/{fname}&quot;)
                lines = content.splitlines()
                if lines:
                    first = lines[0].strip()
                    if first.startswith(&quot;---&quot;):
                        end_fm = content.find(&quot;\n---\n&quot;)
                        if end_fm != -1:
                            fm = content[3:end_fm].strip()
                            preview = fm[:120] + &quot;...&quot; if len(fm)&gt;120 else fm
                        else:
                            preview = first[:120]
                    else:
                        preview = first[:120] + &quot;...&quot; if len(first)&gt;120 else first
            except Exception:
                pass
            table.add_row(fname, preview)
        console.print(table)
    except Exception as e:
        console.print(f&quot;[red]Error in workflows: {e}[/]&quot;)

def main():
    parser = argparse.ArgumentParser(description=&quot;Grok Chat v2.5&quot;)
    parser.add_argument(&quot;--worktree&quot;, default=&quot;.&quot;, help=&quot;Worktree dir&quot;)
    parser.add_argument(&quot;--model&quot;, default=&quot;grok-beta&quot;)
    parser.add_argument(&quot;--max_steps_per_turn&quot;, type=int, default=20)
    parser.add_argument(&quot;--load&quot;, help=&quot;Load chat file&quot;)
    args = parser.parse_args()

    target_dir = Path(args.worktree).resolve()
    os.chdir(target_dir)
    agent = Agent(target_dir=target_dir, model=args.model)

    console.print(Panel(&quot;v2.5 - /help + Full UI! ✨&quot;, title=&quot;🚀&quot;, border_style=&quot;green&quot;))
    console.print(f&quot;[bold cyan]Worktree:[/] {target_dir}&quot;)
    show_help()  # Startup help

    chats_dir = target_dir / &quot;chats&quot;
    chats_dir.mkdir(exist_ok=True)
    session_id = datetime.now().strftime(&quot;%Y%m%d-%H%M%S&quot;)
    chat_file = chats_dir / f&quot;chat-{session_id}.json&quot;
    history = []

    if chat_file.exists():
        with open(chat_file) as f:
            history = json.load(f)
        console.print(f&quot;[green]Resumed {len(history)} turns.[/]&quot;)

    try:
        chat = agent.client.chat.create(model=agent.model, tools=agent.tools)
        chat.append(
            user(
                agent.system_prompt_template.format(
                    directory=str(target_dir), goal=&quot;Interactive chat. Be helpful.&quot;
                )
            )
        )

        while True:
            user_input_raw = get_multiline_input(console)
            if not user_input_raw.strip():
                continue
            cmd = user_input_raw.strip().split()[0].lower()
            if cmd in [&quot;quit&quot;, &quot;exit&quot;, &quot;q&quot;]:
                break
            if cmd == &quot;/help&quot;:
                show_help()
                continue
            if cmd == &quot;/chats&quot;:
                list_chats(target_dir)
                continue
            if cmd == &quot;/subagents&quot;:
                show_subagents(agent)
                continue
            if cmd == &quot;/git&quot;:
                git_status = agent.run_shell(&quot;git status --short&quot;)
                console.print(Panel(git_status, title=&quot;Git&quot;))
                continue
            if cmd == &quot;/costs&quot;:
                summary = get_costs_summary()
                console.print(Panel(summary, title=&quot;💰 API Costs&quot;, border_style=&quot;green&quot;))
                continue
            if cmd == &quot;/skills&quot;:
                skills_dashboard(agent)
                continue
            if cmd == &quot;/tools&quot;:
                tools_dashboard(agent)
                continue
            if cmd == &quot;/workflows&quot;:
                workflows_dashboard(agent)
                continue

            chat.append(user(user_input_raw))
            history.append({&quot;role&quot;: &quot;user&quot;, &quot;content&quot;: user_input_raw})

            step = 1
            max_steps = args.max_steps_per_turn

            with Progress(
                SpinnerColumn(),
                TextColumn(&quot;[progress.description]{task.description}&quot;),
                console=console,
            ) as progress:
                task = progress.add_task(&quot;[cyan]🤖&quot;, total=max_steps)
                while step &lt;= max_steps:
                    progress.update(task, description=f&quot;Step {step}&quot;)
                    msg = chat.sample()
                    log_api_usage(agent.model, getattr(msg, &#x27;usage&#x27;, None))
                    chat.append(msg)
                    history.append(
                        {
                            &quot;role&quot;: &quot;assistant&quot;,
                            &quot;content&quot;: getattr(msg, &quot;content&quot;, &quot;&quot;),
                            &quot;tools&quot;: len(getattr(msg, &quot;tool_calls&quot;, [])),
                        }
                    )

                    if not msg.tool_calls:
                        content = msg.content
                        if &quot;```&quot; in content:
                            console.print(Syntax(content, &quot;markdown&quot;))
                        else:
                            console.print(
                                Panel(
                                    Markdown(content), title=&quot;🤖&quot;, border_style=&quot;cyan&quot;
                                )
                            )
                        break

                    console.print(f&quot;[green]{len(msg.tool_calls)} tools[/]&quot;)
                    for tc in msg.tool_calls:
                        fargs = json.loads(tc.function.arguments)
                        result = agent.tool_map[tc.function.name](**fargs)
                        preview = str(result)[:300] + &quot;...&quot;
                        console.print(
                            Panel(
                                preview, title=tc.function.name, border_style=&quot;yellow&quot;
                            )
                        )
                        chat.append(tool_result(result))
                    step += 1

            with open(chat_file, &quot;w&quot;) as f:
                json.dump(history, f, indent=2)
            console.print(f&quot;[green]💾 {chat_file.name} ({len(history)} turns)[/]&quot;)

            # Persist to ChromaDB
            memory = agent.get_memory()
            if memory:
                agent.memory.add_chat_messages(chat_file.stem, history[-10:])
                console.print(&quot;[green]🧠 Persisted recent chat to ChromaDB[/]&quot;)

    except KeyboardInterrupt:
        console.print(&quot;\nBye!&quot;)
    finally:
        console.print(&quot;[dim]Persistent.[/]&quot;)


if __name__ == &quot;__main__&quot;:
    main()
