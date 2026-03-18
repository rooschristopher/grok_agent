import argparse
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from textual.app import App, ComposeResult, on
from textual.message import Message
from textual.widgets import Footer, Header, Input, RichLog
from xai_sdk.chat import tool_result, user

from agent import Agent

load_dotenv()


class AgentUpdate(Message):
    """Posted by agent worker."""

    def __init__(self, content: str, is_tool: bool = False):
        super().__init__()
        self.content = content
        self.is_tool = is_tool


class TUIChatApp(App):
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
    Header { dock: top; }
    Footer { dock: bottom; }
    """

    BINDINGS = [
        ('ctrl+c', 'quit', 'Quit'),
        ('f1', 'app.toggle_dark_mode', 'Toggle dark'),
    ]

    def __init__(self, target_dir: Path, model: str | None = None):
        self.target_dir = target_dir
        self.model = model
        self.chat = None
        super().__init__()
        self.title = '🤖 Grok Agent TUI'

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield RichLog(id='chat-log')
        yield Input(id='message-input', placeholder='💬 Type msg or /cmd, Enter to send')
        yield Footer()

    def on_mount(self) -> None:
        self.title = f'Grok TUI - {self.target_dir.name}'
        os.chdir(self.target_dir)
        self.chatlog = self.query_one('#chat-log')
        self.user_input = self.query_one('#message-input')
        self.agent = Agent(target_dir=self.target_dir, model=self.model)
        self.chat = self.agent.client.chat.create(model=self.agent.model, tools=self.agent.tools)
        system_prompt = self.agent.system_prompt_template.format(
            directory=str(self.target_dir), goal='Interactive'
        )
        self.chat.append(user(system_prompt))
        self.chatlog.write(f'🚀 [bold green]Ready![/] [cyan]{self.target_dir}[/]')
        self.chatlog.write('[dim]/help for cmds | Enter sends | Rich CLI: grok-chat[/]')

    @on(Input.Submitted)
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        try:
            self.chatlog.write('[dim][debug]Submitted![/]')
            message = event.input.value.strip()
            self.user_input.value = ''
            if not message:
                return
            self.chatlog.write(f'[bold green]You: [/]{message}')
            if message.startswith('/'):
                self.handle_command(message)
                return
            self.chat.append(user(message))
            await self.run_worker(self._agent_turn)
        except Exception as e:
            self.chatlog.write(f'[bold red]Submit err: {e}[/]')

    def handle_command(self, cmd: str) -> None:
        cmd_lower = cmd.strip().lower()
        self.chatlog.write(f'[magenta]Cmd: {cmd}[/]')
        if cmd_lower == '/help':
            self.chatlog.write('''
[bold]Commands:[/]
/help /git /subagents /chats /clear /quit

CLI companion: grok-chat
            ''')
        elif cmd_lower == '/git':
            status = self.agent.git_status()
            self.chatlog.write(f'[yellow]Git:[/] {status}')
        elif cmd_lower == '/subagents':
            subs = self.agent.list_subagents()
            self.chatlog.write(f'[blue]Subs:[/] {subs}')
        elif cmd_lower == '/chats':
            chats_dir = self.target_dir / 'chats'
            if chats_dir.exists():
                chats = [f.name for f in chats_dir.glob('chat-*.json')]
                self.chatlog.write(f'[green]Chats ({len(chats)}):[/] {", ".join(chats) if chats else "none"}')
            else:
                self.chatlog.write('[yellow]No chats/[/]')
        elif cmd_lower == '/clear':
            self.chatlog.clear()
            self.chatlog.write('[dim]Cleared[/]')
        elif cmd_lower in ('/quit', '/q', 'quit'):
            self.exit()
        else:
            self.chatlog.write('[red]Unknown. /help[/]')

    async def _agent_turn(self) -> None:
        max_steps = 20
        for step in range(1, max_steps + 1):
            self.chatlog.write(f'[dim]🤖 Step {step}/{max_steps}...[/]')
            msg = self.chat.sample()
            self.chat.append(msg)
            tool_calls = getattr(msg, 'tool_calls', [])
            if not tool_calls:
                self.post_message(AgentUpdate(msg.content or 'No response'))
                return
            self.chatlog.write(f'[orange]{len(tool_calls)} tools...[/]')
            for tc in tool_calls:
                fname = tc.function.name
                try:
                    fargs = json.loads(tc.function.arguments)
                except (json.JSONDecodeError, AttributeError):
                    fargs = {}
                result = self.agent.tool_map[fname](**fargs)
                self.chat.append(tool_result(result))
                preview = str(result)
                if len(preview) > 300:
                    preview = preview[:300] + '...'
                self.post_message(AgentUpdate(preview, is_tool=True))
        self.post_message(AgentUpdate('Max steps reached'))

    @on(AgentUpdate)
    def on_agent_update(self, event: AgentUpdate) -> None:
        if event.is_tool:
            self.chatlog.write(f'[bold yellow]🛠️ Tool:[/] {event.content}')
        else:
            self.chatlog.write(f'[bold blue]🤖 :[/] {event.content}')


def main():
    parser = argparse.ArgumentParser(description='Grok TUI')
    parser.add_argument('--worktree', default='.', help='Dir')
    parser.add_argument('--model')
    args = parser.parse_args()
    target_dir = Path(args.worktree).resolve()
    app = TUIChatApp(target_dir, args.model)
    app.run()


if __name__ == '__main__':
    main()
