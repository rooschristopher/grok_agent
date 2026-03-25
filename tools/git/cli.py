#!/usr/bin/env python3
import argparse
import os
import subprocess
import sys


def run_cmd(cmd, check=True, capture_output=False):
    """Run shell command."""
    if capture_output:
        return subprocess.run(
            cmd, shell=False, check=check, capture_output=True, text=True
        )
    else:
        return subprocess.run(cmd, shell=False, check=check, text=True)


def main():
    parser = argparse.ArgumentParser(description="Auto-create GitHub PR")
    parser.add_argument(
        "goal", help="Goal/description for PR title (e.g., 'add pr tool')"
    )
    parser.add_argument("--dry-run", action="store_true", help="Dry run: print command")
    parser.add_argument(
        "--body", default="Auto-generated PR from grok_agent.", help="PR body"
    )
    parser.add_argument(
        "--diff-body", action="store_true", help="Append git diff to body"
    )
    parser.add_argument("--title-prefix", default="feat:", help="Title prefix")
    args = parser.parse_args()

    title = f"{args.title_prefix} {args.goal}"

    body = args.body
    if args.diff_body:
        try:
            # Diff from latest commit or from origin/main
            base = subprocess.getoutput(
                "git merge-base HEAD origin/main || git rev-parse HEAD~1"
            ).strip()
            diff = subprocess.getoutput(f"git diff {base}").strip()
            if diff:
                body += f"\n\n### Changes\n```diff\n{diff}\n```"
            else:
                print("No diff found.")
        except:
            print("Could not generate diff.")

    cmd = [
        "gh",
        "pr",
        "create",
        "--title",
        title,
        "--body",
        body,
    ]

    print("Proposed PR:")
    print(f"Title: {title}")
    print(f"Body: {body[:200]}...")

    if args.dry_run:
        print(f"Dry-run command: {' '.join(cmd)}")
        return 0

    confirm = input("\nCreate PR? (y/N): ").strip().lower()
    if confirm != "y":
        print("Aborted.")
        return 1

    print("Creating PR...")
    result = run_cmd(cmd)
    if result.returncode == 0:
        print("PR created successfully!")
        print("Open in browser? (y/N): ", end="")
        if input().strip().lower() == "y":
            os.system("gh pr view --web")
    else:
        print("Failed to create PR.")
        sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())
