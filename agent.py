import os
import json
import subprocess
import sys
import signal
import time
import uuid
import atexit
from pathlib import Path
from typing import Dict, Any, Optional, List
from xai_sdk import Client
from xai_sdk.chat import user, tool, tool_result
from dotenv import load_dotenv
from logger import setup_logging, get_logger
import requests
from tools.code_gen import code_gen_tool, code_gen

# Initialize environment and logging (idempotent)
load_dotenv()
setup_logging("logs/app.log")
logger = get_logger(__name__)

class Agent:
    def __init__(
        self,
        target_dir: Optional[str | Path] = None,
        api_key: Optional[str] = None,
        model: str = "grok-4-1-fast-reasoning",
        tools: Optional[List] = None,
        tool_map: Optional[Dict[str, Any]] = None,
        secondary_system_prompt: Optional[str] = None,
    ) -> None:
        self.target_dir = Path(target_dir or ".").resolve()
        self.agent_script = Path(__file__).resolve()
        self.api_key = api_key or os.getenv("XAI_API_KEY")
        self.client = Client(api_key=self.api_key)
        self.model = model

        self.agent_id = str(uuid.uuid4())
        self.shared_dir = self.target_dir / "agent_shared"
        self.status_file = None
        logger.info("Agent initialized: target_dir=%s model=%s agent_id=%s", self.target_dir, self.model, self.agent_id)

        default_tools = [
            tool(
                name="list_dir",
                description="List files/directories",
                parameters={
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                    "required": [],
                },
            ),
            tool(
                name="read_file",
                description="Read entire file content",
                parameters={
                    "type": "object",
                    "properties": {"filename": {"type": "string"}},
                    "required": ["filename"],
                },
            ),
            tool(
                name="write_file",
                description="Write/overwrite file",
                parameters={
                    "type": "object",
                    "properties": {
                        "filename": {"type": "string"},
                        "content": {"type": "string"},
                        "append": {"type": "boolean"},
                    },
                    "required": ["filename", "content"],
                },
            ),
            tool(
                name="run_shell",
                description="Execute shell command in project directory",
                parameters={
                    "type": "object",
                    "properties": {"cmd": {"type": "string"}},
                    "required": ["cmd"],
                },
            ),
            tool(
                name="spawn_subagent",
                description="Spawn sub-agent for parallel task. Use list_subagents to monitor, kill_subagent if needed.",
                parameters={
                    "type": "object",
                    "properties": {
                        "goal": {"type": "string", "description": "Goal for subagent"},
                        "max_steps": {"type": "integer", "description": "Max steps for subagent"},
                    },
                    "required": ["goal"],
                },
            ),
            tool(
                name="list_subagents",
                description="Get list of all subagents and their statuses.",
                parameters={"type": "object", "properties": {}, "required": []},
            ),
            tool(
                name="kill_subagent",
                description="Terminate a subagent by agent_id.",
                parameters={
                    "type": "object",
                    "properties": {"agent_id": {"type": "string"}},
                    "required": ["agent_id"],
                },
            ),
            tool(
                name="web_search",
                description="Search the web using Google via Serper.dev API. Returns top organic results with titles, snippets, and links. Useful for researching Python errors, libraries, best practices. Example query: 'python TypeError list indices must be integers site:stackoverflow.com'. Requires SERPER_API_KEY in .env (free tier at serper.dev).",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "The search query"},
                        "num_results": {"type": "integer", "description": "Number of top results (default 5, max 10)"}
                    },
                    "required": ["query"],
                },
            ),
            tool(
                name="git_status",
                description="Get git status: lists staged/modified/untracked files.",
                parameters={"type": "object", "properties": {}, "required": []},
            ),
            tool(
                name="git_commit",
                description="Stage all changes and commit with message.",
                parameters={"type": "object", "properties": {"msg": {"type": "string"}}, "required": ["msg"]},
            ),
            tool(
                name="git_diff",
                description="Show git diff for file or unstaged diff.",
                parameters={"type": "object", "properties": {"file": {"type": "string"}}, "required": []},
            ),
            tool(
                name="git_push",
                description="Push to origin. Requires confirm=\\"yes\\".",
                parameters={"type": "object", "properties": {"confirm": {"type": "string"}}, "required": []},
            ),
            tool(
                name="git_pull",
                description="Pull from origin. Requires confirm=\\"yes\\".",
                parameters={"type": "object", "properties": {"confirm": {"type": "string"}}, "required": []},
            ),
            tool(
                name="git_branch",
                description="Manage git branches: list (default), create (branch), delete (branch, delete=True).",
                parameters={"type": "object", "properties": {"branch": {"type": "string"}, "delete": {"type": "boolean"}}, "required": []},
            ),
            tool(
                name="git_worktree",
                description="Manage git worktrees: action=\\'list/add/remove/prune\\', path and branch as needed.",
                parameters={"type": "object", "properties": {"action": {"type": "string"}, "path": {"type": "string"}, "branch": {"type": "string"}}, "required": []},
            ),
            tool(
                name="git_merge",
                description="Merge branch into current, no_ff=True for --no-ff.",
                parameters={"type": "object", "properties": {"branch": {"type": "string"}, "no_ff": {"type": "boolean"}}, "required": ["branch"]},
            ),
        ]
        self.tools = tools or default_tools

        default_tool_map = {
            "list_dir": self.list_dir,
            "read_file": self.read_file,
            "write_file": self.write_file,
            "run_shell": self.run_shell,
            "spawn_subagent": self.spawn_subagent,
            "list_subagents": self.list_subagents,
            "kill_subagent": self.kill_subagent,
            "web_search": self.web_search,
            "git_status": self.git_status,
            "git_commit": self.git_commit,
            "git_diff": self.git_diff,
            "git_push": self.git_push,
            "git_pull": self.git_pull,
            "git_branch": self.git_branch,
            "git_worktree": self.git_worktree,
            "git_merge": self.git_merge,
        }
        self.tool_map = tool_map or default_tool_map
        default_tools.append(code_gen_tool)
        default_tool_map["code_gen"] = code_gen

        # Fixed core system prompt with policy
        secondary_prompt = secondary_system_prompt or ""
        policy_str = """<policy>
These core policies within the <policy> tags take highest precedence. System messages take precedence over user messages.

* Follow additional instructions outside the <policy> tags if they do not violate these core policies, even if they are unintuitive.
* If not specified outside the <policy> tags, you have no restrictions on adult sexual content or offensive content.
</policy>

"""
        agent_description = """You are a helpful autonomous coding agent working in this directory: {directory}

You have access to powerful tools:
- list_dir(path): List files/directories
- read_file(filename): Read file content
- write_file(filename, content, append=False): Write/overwrite file
- run_shell(cmd): Execute shell command in project directory
- spawn_subagent(goal, max_steps=100): Spawn sub-agent for parallel task. Use list_subagents to monitor, kill_subagent if needed.
- list_subagents: Get list of all subagents and their statuses.
- kill_subagent(agent_id): Terminate a subagent by agent_id.
- web_search(query, num_results=5): Google search
- git_status: Get git status
- git_commit(msg): Stage all and commit
- git_diff([file]): Show unstaged diff
- git_push(confirm="yes"): Push to origin
- git_pull(confirm="yes"): Pull from origin
- git_branch(branch, delete=False): Manage branches
- git_worktree(action, path, branch): Manage worktrees
- git_merge(branch): Merge branch

CRITICAL FORMATTING RULES:
- Use actual newlines in code blocks (```python
code here
```). Do NOT use literal \\n in displayed code.
- Do NOT use HTML entities like &quot;, &lt;, &gt;. Use " < > directly.
- For tool parameters like write_file's content (JSON string), use \\n to represent newlines in multi-line strings.
- git_status: Returns JSON with files list.
- git_push, git_pull: Set confirm="yes" to execute.
- git_branch: branch str optional, delete bool for delete.
- git_worktree: action 'list/add/remove/prune', path/branch as needed.
- git_merge: branch required, no_ff optional bool.

Think step-by-step. Use tools when needed to assist the user.
For complex tasks, spawn subagents.
Be concise, helpful, and use FINAL ANSWER when completing a goal.

Goal: {goal}"""
        self.system_prompt_template = policy_str + secondary_prompt + agent_description

        atexit.register(self._cleanup_status)

    def _ensure_shared_dir(self) -> None:
        self.shared_dir.mkdir(exist_ok=True, parents=True)

    def _cleanup_status(self) -> None:
        if self.status_file and self.status_file.exists():
            try:
                self.status_file.unlink()
            except Exception:
                pass

    def update_status(self, status: str, output: str = "", data: dict = None) -> None:
        self._ensure_shared_dir()
        if self.status_file is None:
            self.status_file = self.shared_dir / f"{self.agent_id}.json"
        data = data or {}
        info = {
            "agent_id": self.agent_id,
            "status": status,
            "output": output,
            "pid": os.getpid(),
            "data": data,
            "timestamp": time.time(),
        }
        try:
            self.status_file.write_text(json.dumps(info, default=str), encoding='utf-8')
        except Exception as e:
            logger.error("Status update failed: %s", e)

    def list_dir(self, path: str = ".") -> str:
        try:
            p = self.target_dir / path
            items = [item.name for item in p.iterdir()]
            return json.dumps({"path": str(p), "items": sorted(items)})
        except Exception as e:
            return json.dumps({"error": str(e)})

    def read_file(self, filename: str) -> str:
        path = self.target_dir / filename
        if not path.is_file():
            return json.dumps({"error": f"File not found: {path}"})
        try:
            return path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            return json.dumps({"error": str(e)})

    def write_file(self, filename: str, content: str, append: bool = False) -> str:
        path = self.target_dir / filename
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            mode = 'a' if append else 'w'
            with path.open(mode, encoding='utf-8') as f:
                f.write(content)
            return json.dumps({"status": "ok", "path": str(path)})
        except Exception as e:
            return json.dumps({"error": str(e)})

    def run_shell(self, cmd: str) -> str:
        try:
            r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30, cwd=str(self.target_dir))
            return json.dumps({
                "stdout": r.stdout.strip(),
                "stderr": r.stderr.strip(),
                "returncode": r.returncode,
            })
        except Exception as e:
            return json.dumps({"error": str(e)})

    def spawn_subagent(self, goal: str, max_steps: int = 100) -> str:
        self._ensure_shared_dir()
        agent_id = str(uuid.uuid4())
        status_file = self.shared_dir / f"{agent_id}.json"
        init_status = {
            "agent_id": agent_id,
            "status": "spawning",
            "goal": goal[:100],
            "timestamp": time.time()
        }
        status_file.write_text(json.dumps(init_status, default=str), encoding='utf-8')
        cmd = [
            sys.executable,
            str(self.agent_script),
            "--target_dir", str(self.target_dir),
            "--agent_id", agent_id,
            "--goal", goal,
            "--max_steps", str(max_steps)
        ]
        p = subprocess.Popen(cmd, cwd=str(self.target_dir))
        time.sleep(0.3)
        try:
            st = json.loads(status_file.read_text())
            st["pid"] = p.pid
            st["status"] = "running"
            status_file.write_text(json.dumps(st, default=str), encoding='utf-8')
        except Exception:
            pass
        result = {"agent_id": agent_id, "pid": p.pid}
        self.update_status("spawned", f"{agent_id}", result)
        return json.dumps(result)

    def list_subagents(self) -> str:
        agents = []
        if self.shared_dir.exists():
            for status_file in self.shared_dir.glob("*.json"):
                if status_file.name == f"{self.agent_id}.json":
                    continue
                try:
                    st = json.loads(status_file.read_text())
                    agents.append(st)
                except Exception as e:
                    logger.warning("Failed to parse %s: %s", status_file.name, e)
        return json.dumps({"subagents": agents})

    def kill_subagent(self, agent_id: str) -> str:
        status_file = self.shared_dir / f"{agent_id}.json"
        if not status_file.exists():
            return json.dumps({"error": "Agent not found"})
        try:
            st = json.loads(status_file.read_text())
            if "pid" not in st:
                return json.dumps({"error": "No PID in status"})
            os.kill(st["pid"], signal.SIGTERM)
            self.update_status("killed", agent_id)
            return json.dumps({"status": "kill_sent", "agent_id": agent_id})
        except Exception as e:
            return json.dumps({"error": str(e)})

    def web_search(self, query: str, num_results: int = 5) -> str:
        api_key = os.getenv("SERPER_API_KEY")
        if not api_key:
            return json.dumps({"error": "SERPER_API_KEY not set. Sign up at https://serper.dev for free API key and add to .env"})
        try:
            url = "https://google.serper.dev/search"
            payload = {
                "q": query,
                "num": min(num_results, 10)
            }
            headers = {
                "X-API-KEY": api_key,
                "Content-Type": "application/json"
            }
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            results = []
            for item in data.get("organic", [])[:num_results]:
                title = item.get("title", "")[:100] + "..." if len(item.get("title", "")) > 100 else item.get("title", "")
                snippet = item.get("snippet", "")[:200] + "..." if len(item.get("snippet", "")) > 200 else item.get("snippet", "")
                link = item.get("link", "")
                results.append(f"**{title}\\n{snippet}\\n[Source]({link})\\n")
            summary = "\\n---\\n".join(results)
            return json.dumps({
                "query": query,
                "num_results": len(results),
                "summary": summary,
                "raw_results": data.get("organic", [])[:num_results]
            })
        except Exception as e:
            return json.dumps({"error": f"Web search failed: {str(e)}"})
    def git_status(self) -> str:
        try:
            result = subprocess.run([
                "git", "status", "--porcelain"],
                cwd=str(self.target_dir),
                capture_output=True,
                text=True,
                check=True,
            )
            files = []
            for line in result.stdout.splitlines():
                if line and len(line) >= 3 and line[2] == " ":
                    status = line[:2]
                    filename = line[3:].lstrip()
                    files.append({"filename": filename, "status": status})
            return json.dumps({"files": files})
        except (subprocess.CalledProcessError, FileNotFoundError):
            return json.dumps({"files": []})

    def git_commit(self, msg: str) -> str:
        try:
            status_result = subprocess.run([
                "git", "status", "--porcelain"],
                cwd=str(self.target_dir),
                capture_output=True,
                text=True,
                check=False,
            )
            files = []
            for line in status_result.stdout.splitlines():
                if line and len(line) >= 3 and line[2] == " ":
                    status = line[:2]
                    filename = line[3:].lstrip()
                    files.append({"filename": filename, "status": status})
            if not files:
                return json.dumps({"success": False})
            subprocess.run(["git", "add", "."], cwd=str(self.target_dir), check=True, capture_output=True)
            subprocess.run([
                "git", "commit", "-m", msg],
                cwd=str(self.target_dir),
                capture_output=True,
                text=True,
                check=True,
            )
            return json.dumps({"success": True, "files": files})
        except (subprocess.CalledProcessError, FileNotFoundError):
            return json.dumps({"success": False})

    def git_diff(self, file: Optional[str] = None) -> str:
        cmd = ["git", "diff"]
        if file:
            cmd.append(file)
        try:
            result = subprocess.run(cmd, cwd=str(self.target_dir), capture_output=True, text=True)
            return result.stdout
        except Exception as e:
            return json.dumps({"error": str(e)})

    def git_push(self, confirm: Optional[str] = None) -> str:
        if confirm != "yes":
            return json.dumps({"confirm": "Push to origin HEAD"})
        try:
            result = subprocess.run(["git", "push"], cwd=str(self.target_dir), capture_output=True, text=True)
            return json.dumps({
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "returncode": result.returncode,
            })
        except Exception as e:
            return json.dumps({"error": str(e)})

    def git_pull(self, confirm: Optional[str] = None) -> str:
        if confirm != "yes":
            return json.dumps({"confirm": "Pull from origin master"})
        try:
            result = subprocess.run(["git", "pull"], cwd=str(self.target_dir), capture_output=True, text=True)
            return json.dumps({
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "returncode": result.returncode,
            })
        except Exception as e:
            return json.dumps({"error": str(e)})

    def git_branch(self, branch: Optional[str] = None, delete: bool = False) -> str:
        try:
            cmd = ["git", "branch"]
            if delete and branch:
                cmd.extend(["-D", branch])
            elif branch:
                cmd.append(branch)
            result = subprocess.run(cmd, cwd=str(self.target_dir), capture_output=True, text=True, check=True)
            return json.dumps({"stdout": result.stdout.strip(), "success": True})
        except subprocess.CalledProcessError as e:
            stderr = e.stderr.strip() if e.stderr else ""
            return json.dumps({"error": stderr or str(e), "success": False})
        except Exception as e:
            return json.dumps({"error": str(e)})

    def git_worktree(self, action: str = "list", path: Optional[str] = None, branch: Optional[str] = None) -> str:
        try:
            cmd = ["git", "worktree"]
            if action == "list":
                cmd.append("list")
            elif action == "add":
                if not path or not branch:
                    return json.dumps({"error": "path and branch required for add"})
                cmd.extend(["add", path, branch])
            elif action == "remove":
                if not path:
                    return json.dumps({"error": "path required for remove"})
                cmd.extend(["remove", path])
            elif action == "prune":
                cmd.append("prune")
            else:
                return json.dumps({"error": f"Unknown action: {action}"})
            result = subprocess.run(cmd, cwd=str(self.target_dir), capture_output=True, text=True, check=True)
            return json.dumps({"stdout": result.stdout.strip(), "success": True})
        except subprocess.CalledProcessError as e:
            stderr = e.stderr.strip() if e.stderr else ""
            return json.dumps({"error": stderr or str(e), "success": False})
        except Exception as e:
            return json.dumps({"error": str(e)})

    def git_merge(self, branch: str, no_ff: bool = False) -> str:
        try:
            cmd = ["git", "merge"]
            if no_ff:
                cmd.append("--no-ff")
            cmd.append(branch)
            result = subprocess.run(cmd, cwd=str(self.target_dir), capture_output=True, text=True, check=True)
            return json.dumps({"stdout": result.stdout.strip(), "success": True})
        except subprocess.CalledProcessError as e:
            stderr = e.stderr.strip() if e.stderr else ""
            return json.dumps({"error": stderr or str(e), "success": False})
        except Exception as e:
            return json.dumps({"error": str(e)})

    def run(self, goal: str, max_steps: int = 200) -> None:
        self._goal = goal
        logger.info("Starting agent run: goal=%s max_steps=%d", goal, max_steps)
        self.update_status("starting", goal[:100])
        try:
            chat = self.client.chat.create(model=self.model, tools=self.tools)
        except Exception as e:
            logger.error("Failed to create chat: %s", e)
            self.update_status("error", str(e))
            print(f"Setup error: {e}")
            return
        chat.append(
            user(
                self.system_prompt_template.format(directory=str(self.target_dir), goal=goal)
            )
        )
        for step in range(max_steps):
            logger.debug("Sampling model response (step=%d)", step + 1)
            try:
                msg = chat.sample()
            except Exception as e:
                logger.error("API sample failed: %s", e)
                self.update_status("error", f"Sample failed: {e}")
                print(f"Agent stopped: API error - {e}")
                return
            chat.append(msg)
            self.update_status("running", f"step {step+1}", {"step": step + 1})
            has_tools = bool(getattr(msg, "tool_calls", None))
            logger.debug("Received message (step=%d) has_tools=%s", step + 1, has_tools)
            if not has_tools:
                content = getattr(msg, "content", "")
                self.update_status("done", content)
                logger.info("Final response produced at step=%d length=%d", step + 1, len(str(content)))
                print("\n" + "=" * 50)
                print("FINAL RESPONSE:")
                print(content)
                return
            print(f"\nStep {step + 1} — tool calls: {len(msg.tool_calls)}")
            logger.info("Step %d: processing %d tool call(s)", step + 1, len(msg.tool_calls))
            for tc in msg.tool_calls:
                name = getattr(getattr(tc, "function", tc), "name", None)
                raw_args = getattr(getattr(tc, "function", tc), "arguments", "{}")
                try:
                    args = json.loads(raw_args) if isinstance(raw_args, str) else (raw_args or {})
                except Exception:
                    args = {}
                print(f"  → {name} {args}")
                logger.debug("Tool call: name=%s args=%s", name, args)
                try:
                    handler = self.tool_map.get(name)
                    if handler is None:
                        result = json.dumps({"error": f"Unknown tool: {name}"})
                        logger.warning("Unknown tool requested: %s", name)
                    else:
                        result = handler(**args)
                        logger.debug("Tool executed: %s", name)
                except Exception as e:
                    logger.exception("Tool execution failed: %s", name)
                    result = json.dumps({"error": str(e)})
                chat.append(tool_result(result))
                preview = result[:120] + ("…" if len(result) > 120 else "")
                print(f"  ← {preview}")
                logger.debug("Tool result preview: %s", preview)
        logger.warning("Max steps reached without final response. Stopping.")
        self.update_status("timeout", "Max steps reached")
        print("\nMax steps reached — stopping.")


if __name__ == "__main__":
    import argparse
    from pathlib import Path
    parser = argparse.ArgumentParser(description="Autonomous Coding Agent")
    parser.add_argument("--target_dir", default=".")
    parser.add_argument("--agent_id")
    parser.add_argument("--goal")
    parser.add_argument("--max_steps", type=int, default=2000)
    parser.add_argument("--model", default="grok-4-1-fast-reasoning")
    args = parser.parse_args()
    target_dir = Path(args.target_dir).resolve()
    agent = Agent(target_dir=target_dir, model=args.model)
    if args.agent_id:
        agent.agent_id = args.agent_id
    goal = args.goal or """
"""
    agent.run(goal, max_steps=args.max_steps)
