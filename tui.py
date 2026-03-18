import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from rich.syntax import Syntax
from textual.app import App, ComposeResult, on
from textual.containers import Container, Horizontal, VerticalScroll
from textual.message import Message
from textual.timer import Timer
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    RichLog,
    Select,
    Static,
    TextArea,
)
from xai_sdk.chat import tool_result, user

from agent import Agent

load_dotenv()


class AgentUpdate(Message):
    def __init__(self, content: str, is_tool: bool = False, is_code: bool = False):
        super().__init__()
        self.content = content
        self.is_tool = is_tool
        self.is_code = is_code


class TUIChatApp(App):
    CSS = """
    Screen {
        layout: horizontal;
    }
    #sidebar {
        width: 30;
        background: $panel;
        padding: 1;
        border-right: solid $primary;
    }
    #chat-area {
        height: 1fr;
        layout: vertical;
    }
    #chatlog {
        height: 1fr;
        overflow-y: scroll;
    }
    #input-area {
        height: auto;
        dock: bottom;
        background: $background;
    }
    #msg-area {
        width: 1fr;
        height: 4;
    }
    #btn-send {
        margin-left: 1;
        @media (mobile) {
            dock: bottom;
        }
    }
    DataTable {
        height: 1fr;
        border: none;
    }
    """

    BINDINGS = [
        ('ctrl+c', 'quit', 'Quit'),
        ('f1', 'toggle_dark', 'Toggle dark'),
        ('ctrl+k', 'focus_cmd_palette', 'Cmd palette'),
    ]

    def __init__(self, target_dir: Path, model: str | None = None):
        self.target_dir = target_dir
        self.model = model or "grok-beta"
        self.chat = None
        self.agent = None
        self.subagents_timer = None
        self.messages: List[dict] = []
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Horizontal(
            Container(
                Label("🛠️ Tools & Subs", id="sidebar-title"),
                Button("Git Status", id="btn-git"),
                Button("Subagents", id="btn-subs"),
                Button("Skills", id="btn-skills"),
                Button("Jira", id="btn-jira"),
                DataTable(id="subs-table"),
                classes="sidebar",
                id="sidebar",
            ),
            Container(
                VerticalScroll(RichLog(id="chatlog"), id="chat-area"),
                Container(
                    TextArea(placeholder="💬 Multi-line msg or /cmd...", id="msg-area"),
                    Button("Send ➤", id="btn-send", variant="primary"),
                    id="input-area",
                ),
                id="main-chat",
            ),
            id="main-layout",
        )
        yield Footer()

    def on_mount(self) -> None:
        self.title = f"Grok TUI - {self.target_dir.name}"
        os.chdir(self.target_dir)
        self.agent = Agent(target_dir=self.target_dir, model=self.model)
        self.chat = self.agent.client.chat.create(model=self.agent.model, tools=self.agent.tools)
        system_prompt = self.agent.system_prompt_template.format(
            directory=str(self.target_dir), goal="Interactive"
        )
        self.chat.append(user(system_prompt))
        self.chatlog = self.query_one("#chatlog", RichLog)
        self.msg_area = self.query_one("#msg-area", TextArea)
        self.subs_table = self.query_one("#subs-table", DataTable)
        self.subs_table.add_columns("ID", "Status", "Goal")
        self.update_subagents()
        self.subagents_timer = self.set_interval(5, self.update_subagents)
        self.chatlog.write("🚀 Super TUI ready! Multi-line, sidebar, live subs!")
        self.chatlog.write("[dim]Type /help in input | Send btn | F1 dark[/]")

    def update_subagents(self) -> None:
        subs = json.loads(self.agent.list_subagents()).get("subagents", [])
        self.subs_table.clear()
        for sub in subs[:10]:
            self.subs_table.add_row(
                sub.get("agent_id", "")[:8],
                sub.get("status", "unknown"),
                sub.get("goal", "")[:40],
            )

    def log_message(self, role: str, content: str, timestamp: bool = True):
        ts = f" [{datetime.now().strftime('%H:%M')}]" if timestamp else ""
        self.chatlog.write(f"[bold { 'green' if role=='user' else 'blue' }]{role.upper()}:{ts}[/] {content}")

    @on(Button.Pressed, "#btn-send")
    async def on_send(self) -> None:
        message = self.msg_area.text.strip()
        if not message:
            return
        self.msg_area.text = ""
        self.log_message("user", message)
        if message.startswith("/"):
            self.handle_command(message)
            return
        self.chat.append(user(message))
        self.run_worker(self._agent_turn)

    @on(Button.Pressed, "#btn-git")
    def on_git(self):
        status = self.agent.git_status()
        self.chatlog.write(f"[yellow]Git Status:[/] {status}")

    @on(Button.Pressed, "#btn-subs")
    def on_subs(self):
        self.update_subagents()

    @on(Button.Pressed, "#btn-skills")
    def on_skills(self):
        # From chat.py logic
        self.chatlog.write("[blue]Skills dashboard (simplified)[/]")
        # Expand with agent.read_file etc.

    @on(Button.Pressed, "#btn-jira")
    def on_jira(self):
        result = self.agent.run_shell("python tools/jira/cli.py list-my")
        self.chatlog.write(f"[green]Jira:[/] {result}")

    def handle_command(self, cmd: str) -> None:
        cmd_lower = cmd.strip().lower()
        self.chatlog.write(f"[magenta]Cmd: {cmd}[/]")
        # Expanded from before
        if cmd_lower == '/help':
            self.chatlog.write("""
Commands & Buttons:
/help git subagents skills jira clear
Multi-line OK | Syntax highlight | Live subs refresh
            """)
        elif cmd_lower == '/clear':
            self.chatlog.clear()
            self.chatlog.write("[dim]Cleared[/]")
        elif cmd_lower == '/model':
            self.chatlog.write("[dim]Model switch in future update[/]")
        else:
            self.chatlog.write("[red]Unknown[/]")

    async def _agent_turn(self) -> None:
        max_steps = 20
        for step in range(1, max_steps + 1):
            self.chatlog.write(f"[dim]Step {step}/{max_steps}...[/]")
            msg = self.chat.sample()
            self.chat.append(msg)
            tool_calls = getattr(msg, 'tool_calls', [])
            if not tool_calls:
                content = msg.content or 'No response'
                self.post_message(AgentUpdate(content))
                return
            self.chatlog.write(f"[orange]{len(tool_calls)} tools...[/]")
            for tc in tool_calls:
                fname = tc.function.name
                try:
                    fargs = json.loads(tc.function.arguments)
                except:
                    fargs = {}
                result = self.agent.tool_map[fname](**fargs)
                self.chat.append(tool_result(result))
                preview = str(result)[:300] + '...' if len(str(result)) > 300 else str(result)
                self.post_message(AgentUpdate(preview, is_tool=True))
        self.post_message(AgentUpdate('Max steps reached'))

    @on(AgentUpdate)
    def on_agent_update(self, event: AgentUpdate) -> None:
        if event.is_tool:
            self.chatlog.write(f"[bold yellow]🛠️ {event.content}[/]")
        else:
            self.chatlog.write(f"[bold blue]🤖 {event.content}[/]")

    def on_destroy(self) -> None:
        if self.subagents_timer:
            self.subagents_timer.stop()


def main():
    parser = argparse.ArgumentParser(description='Super Grok TUI')
    parser.add_argument('--worktree', default='.', help='Dir')
    parser.add_argument('--model')
    args = parser.parse_args()
    target_dir = Path(args.worktree).resolve()
    app = TUIChatApp(target_dir, args.model)
    app.run()


if __name__ == '__main__':
    main()
