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
                            preview = fm[:120] + "..." if len(fm)>120 else fm
                        else:
                            preview = first[:120]
                    else:
                        preview = first[:120] + "..." if len(first)>120 else first
            except:
                pass
            table.add_row(fname, preview)
        console.print(table)
    except Exception as e:
        console.print(f"[red]Error in workflows: {e}[/]")


def main():
    parser = argparse.ArgumentParser(description="Grok Chat v2.5")
    parser.add_column("--worktree", default=".", help="Worktree dir")
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
                    log_api_usage(agent.model, getattr(msg, 'usage', None))
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