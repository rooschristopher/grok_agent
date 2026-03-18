import argparse
import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from textual.app import App, ComposeResult, on
from textual.message import Message
from textual.widgets import Footer, Header, Input, RichLog
from textual.worker import Worker
from xai_sdk.chat import tool_result, user

from agent import Agent

load_dotenv()


class AgentUpdate(Message):
    """Message posted by agent worker."""

    def __init__(self, content: str, is_tool: bool = False):
        super().__init__()
        self.content = content
        self.is_tool = is_tool


class TUIChatApp(App):
    """Grok Agent Textual TUI."""

    CSS = """
    RichLog#chat-log {
        height: 1fr;
        border: round $primary;
        margin: 1;
    }
    Input#message-input {
        dock: bottom;
        height: 3;
        margin: 1;
    }
    Header {
        dock: top;
    }
    Footer {
        dock: bottom;
    }
    """

    BINDINGS = [
        ("ctrl+c", "quit", "Quit"),
        ("f1", "toggle_dark", "Toggle theme"),
    ]

    def __init__(self, target_dir: Path, model: str | None = None):
        self.target_dir = target_dir
        self.model = model
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Header("🤖 Grok Agent TUI v1.0", show_clock=True)
        yield RichLog(id="chat-log")
        yield Input(
            "💬 Message or /cmd...",
            id="message-input",
            placeholder="Press Enter to send",
        )
        yield Footer()

    def on_mount(self) -> None:
        os.chdir(self.target_dir)
        self.log: RichLog = self.query_one(RichLog)
        self.input: Input = self.query_one(Input)
        self.agent = Agent(target_dir=self.target_dir, model=self.model)
        self.chat = self.agent.client.chat.create(
            model=self.agent.model,
            tools=self.agent.tools
        )
        system_prompt = self.agent.system_prompt_template.format(
            directory=str(self.target_dir),
            goal="Interactive"
        )
        self.chat.append(user(system_prompt))
        self.log.write("🚀 [bold green]TUI loaded![/] Worktree: [bold cyan]{}[/]".format(self.target_dir))
        self.log.write("[dim italic]Type [bold]/help[/] for commands. Rich CLI in [code]grok-chat[/].[/]")

    @on(Input.Submitted)
    def on_input_submitted(self, event: Input.Submitted):
        message = event.input.value.strip()
        self.input.value = ""
        if not message:
            return
        self.log.write(f"[bold green]👤 You:[/] {message}")
        if message.startswith('/'):
            self.handle_command(message)
            return
        self.chat.append(user(message))
        self.run_agent_turn()

    def handle_command(self, cmd: str) -> None:
        cmd_lower = cmd.strip().lower()
        self.log.write(f"[magenta]🛠️ {cmd}[/]")
        if cmd_lower == '/help':
            self.log.write("""
[b]Commands:[/]
/help    - Show this
/git     - Git status
/subagents - Subagents status
/chats   - List sessions
/clear   - Clear chat log
/quit    - Quit app

[dim]More dashboards in grok-chat (CLI).[/]
            """)
        elif cmd_lower == '/git':
            status = self.agent.git_status()
            self.log.write(f"[yellow]Git status:[/] [code]{status}[/]")
        elif cmd_lower == '/subagents':
            subs = self.agent.list_subagents()
            self.log.write(f"[blue]Subagents:[/] [code]{subs}[/]")
        elif cmd_lower == '/chats':
            chats_dir = self.target_dir / 'chats'
            if chats_dir.exists():
                chats = [f.name async for f in chats_dir.glob('chat-*.json')]
                self.log.write(f"[green]Chats ({len(chats)}):[/] {', '.join(chats) or 'none'}")
            else:
                self.log.write('[yellow]No chats/ dir[/]')
        elif cmd_lower == '/clear':
            self.log.clear()
            self.log.write('[dim]Log cleared[/]')
        else:
            self.log.write('[red]Unknown cmd. /help[/]')

    def run_agent_turn(self) -> None:
        self.agent_worker = self.create_worker(self._agent_worker)
        self.agent_worker.spun.connect(lambda w: self.log.write('[dim]🤖 Thinking...[/]'))
        self.agent_worker.killed.connect(lambda _: self.log.write('[green]✅ Turn done.[/]'))
        self.post_message_to(self.agent_worker, Worker.Started())  # Start it
        self.agent_worker.start()

    async def _agent_worker(self, worker: Worker):
        max_steps = 20
        for step in range(1, max_steps + 1):
            worker.set_state(f'Step {step}/{max_steps}')
            msg = self.chat.sample()
            self.chat.append(msg)
            tool_calls = getattr(msg, 'tool_calls', [])
            if not tool_calls:
                worker.post_message(AgentUpdate(msg.content or '[gray]No response.[/]'))
                return
            self.log.write(f'[orange]🔧 Running {len(tool_calls)} tools...[/]')
            for tc in tool_calls:
                fname = tc.function.name
                fargs_str = tc.function.arguments
                try:
                    fargs = json.loads(fargs_str)
                except:
                    fargs = {}
                result = self.agent.tool_map[fname](**fargs)
                self.chat.append(tool_result(result))
                preview = str(result)
                if len(preview) > 300:
                    preview = preview[:300] + '...'
                worker.post_message(AgentUpdate(preview, is_tool=True))
            await worker.yield_if_needed()
        worker.post_message(AgentUpdate('[yellow]Max steps reached.[/]'))

    @on(AgentUpdate)
    def on_agent_update(self, event: AgentUpdate) -> None:
        if event.is_tool:
            self.log.write(f'[bold yellow]🛠️ Tool result:[/] {event.content}')
        else:
            self.log.write(f'[bold blue]🤖 AI:[/] {event.content}')


def main():
    parser = argparse.ArgumentParser(description='Grok Agent TUI (textual)')
    parser.add_argument('--worktree', default='.', help='Project/worktree dir')
    parser.add_argument('--model')
    args = parser.parse_args()
    target_dir = Path(args.worktree).resolve()
    app = TUIChatApp(target_dir=target_dir, model=args.model)
    app.run()


if __name__ == '__main__':
    main()
