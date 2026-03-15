import argparse
import subprocess
import os
from pathlib import Path
from dotenv import load_dotenv
from xai_sdk import Client
from xai_sdk.chat import user
from rich.console import Console
from rich.panel import Panel

load_dotenv()
console = Console()
client = Client(api_key=os.getenv("XAI_API_KEY"))
MODEL = os.getenv("GROK_MODEL", "grok-2")

def generate_code(chat_prompt: str) -> str:
    chat = client.chat.create(model=MODEL)
    chat.append(user(chat_prompt))
    msg = chat.sample()
    content = msg.content or ""
    # Strip code block markers
    if "```python" in content.lower():
        lines = content.splitlines()
        start_i = 0
        for i, line in enumerate(lines):
            if "```python" in line.lower():
                start_i = i + 1
                break
        end_i = len(lines)
        for i in range(start_i, len(lines)):
            if "```" in lines[i].lower():
                end_i = i
                break
        content = "\n".join(lines[start_i:end_i]).strip()
    return content

def main():
    parser = argparse.ArgumentParser(description="Autonomous TDD using Grok")
    parser.add_argument("--spec", required=True, help="Feature specification")
    parser.add_argument("--module", required=True, help="Module path e.g. utils.calc (without .py)")
    parser.add_argument("--max-iters", type=int, default=10)
    args = parser.parse_args()

    impl_file = Path(args.module + ".py")
    test_file = Path("tests", f"test_{args.module}.py")

    impl_file.parent.mkdir(exist_ok=True, parents=True)
    test_file.parent.mkdir(exist_ok=True, parents=True)

    # Red phase
    test_prompt = f"""Generate comprehensive pytest unit tests for module '{args.module}'.

Specification:
{args.spec}

Output ONLY the code for tests/test_{args.module}.py"""
    console.print(Panel("🟥 RED: Generating tests", title="TDD"))
    tests_code = generate_code(test_prompt)
    test_file.write_text(tests_code, encoding="utf-8")
    console.print(f"[green]Tests written: {test_file}[/green]")

    # Green loop
    for i in range(1, args.max_iters + 1):
        console.print(Panel(f"🟩 GREEN #{i}: Testing", title="TDD"))
        result = subprocess.run(["pytest", str(test_file), "-v", "--tb=short"], text=True, capture_output=True, cwd=".")
        if result.returncode == 0:
            console.print(Panel("✅ GREEN: Tests pass!", title="TDD", style="green"))
            # REFACTOR PHASE
            console.print(Panel("🔄 REFRACTOR: Improving code quality", title="TDD", style="blue"))
            current_impl = impl_file.read_text(encoding="utf-8")
            tests_content = test_file.read_text(encoding="utf-8")
            refactor_prompt = f"""Refactor the implementation to make it cleaner, more readable, efficient, and follow Python best practices.
Ensure it still passes all the tests.
Module: {args.module}
Tests (must pass after refactor):
```
{tests_content}
```
Current implementation:
```
{current_impl}
```
Output ONLY the complete refactored code for '{args.module}.py'. No other text."""
            refactored_code = generate_code(refactor_prompt)
            impl_file.write_text(refactored_code, encoding="utf-8")
            console.print(f"[cyan]Refactored implementation written to {impl_file}[/cyan]")
            # Verify refactor
            console.print(Panel("🧪 VERIFY: Re-run tests after refactor", title="TDD"))
            verify_result = subprocess.run(["pytest", str(test_file), "-v", "--tb=short"], text=True, capture_output=True, cwd=".")
            if verify_result.returncode == 0:
                console.print(Panel("🎉 REFACTOR SUCCESS! Tests still pass.", title="TDD", style="bright_green"))
            else:
                console.print(Panel("⚠️ Refactor broke tests. Reverting to green version.", title="TDD", style="yellow"))
                impl_file.write_text(current_impl, encoding="utf-8")
                console.print(Panel("✅ Reverted. Original green code preserved.", title="TDD", style="green"))
            return
        failures = result.stdout + result.stderr
        current_code = impl_file.read_text(encoding="utf-8") if impl_file.exists() else ""
        fix_prompt = f"""Implement '{args.module}.py' to pass these tests:
Tests:
```
{test_file.read_text(encoding="utf-8")}
```
Failures:
```
{failures}
```
Current code:
```
{current_code}
```
Output ONLY the code for '{args.module}.py'."""
        console.print(Panel("🖊️ Generate implementation", title="TDD"))
        new_code = generate_code(fix_prompt)
        impl_file.write_text(new_code, encoding="utf-8")
        console.print(f"[blue]Implementation updated: {impl_file}[/blue]")
    console.print(Panel("⚠️ Max iterations reached without green", title="TDD", style="yellow"))

if __name__ == "__main__":
    main()