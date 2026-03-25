#!/usr/bin/env python
"""
Skills Loader CLI - OpenCode-like skill management.
Supports skills/ and .grok_agent/skills/ directories.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table

SKILLS_DIRS: list[Path] = [
    Path("skills"),
    Path(".grok_agent/skills"),
]


def parse_frontmatter(file_path: Path) -> dict[str, Any] | None:
    """Parse YAML frontmatter from .md skill file."""
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return None

    if content.startswith("---\n"):
        parts = content.split("---\n", 2)
        if len(parts) >= 2 and parts[1].strip():
            try:
                fm = yaml.safe_load(parts[1]) or {}
                fm = dict(fm)
                fm["file_path"] = file_path
                fm["full_content"] = parts[2].strip() if len(parts) > 2 else ""

                # Normalize keywords
                keywords = fm.get("keywords", [])
                if isinstance(keywords, str):
                    keywords = [k.strip() for k in keywords.split(",")]
                fm["keywords"] = keywords

                return fm
            except yaml.YAMLError:
                pass

    # Fallback
    return {
        "name": file_path.stem.replace(".SKILL", "").replace("-", " ").title(),
        "description": "Skill without YAML frontmatter.",
        "keywords": [],
        "file_path": file_path,
        "full_content": content,
    }


def get_all_skills() -> tuple[dict[str, int], list[dict[str, Any]]]:
    """Find and parse all skills."""
    stats: dict[str, int] = {"dirs_checked": 0, "md_files": 0, "parsed": 0}
    all_skills: list[dict[str, Any]] = []

    for skills_dir in SKILLS_DIRS:
        if skills_dir.is_dir():
            stats["dirs_checked"] += 1
            md_files = [
                f
                for f in skills_dir.iterdir()
                if f.is_file() and f.suffix.lower() == ".md"
            ]
            stats["md_files"] += len(md_files)
            for file_path in md_files:
                fm = parse_frontmatter(file_path)
                fm["rel_path"] = f"{skills_dir.name}/{file_path.name}"
                all_skills.append(fm)
                stats["parsed"] += (
                    1
                    if "name" in fm
                    and fm["name"]
                    != file_path.stem.replace(".SKILL", "").replace("-", " ").title()
                    else 0
                )  # rough yamls

    return stats, all_skills


def print_dashboard(
    stats: dict[str, int], skills: list[dict[str, Any]], console: Console
):
    """Print rich dashboard."""
    console.print("[bold cyan]🧠 Skills Dashboard[/bold cyan]")
    console.print(
        f"[dim]📊 Stats: {stats['dirs_checked']} dirs | {stats['md_files']} MD files | {len(skills)} parsed[/dim]\n"
    )

    if not skills:
        console.print("[yellow]No skills found.[/yellow]")
        return

    table = Table(title="Skills List", show_header=True, header_style="bold magenta")
    table.add_column("🧠 Name", style="cyan", no_wrap=True)
    table.add_column("🔖 Keywords", style="magenta")
    table.add_column("📝 Description", style="green")
    table.add_column("📁 Path", style="blue")

    for skill in skills:
        name = skill.get("name", "Unnamed")
        keywords_str = " | ".join(skill.get("keywords", []))
        desc = skill.get("description", "")[:60]
        if len(skill.get("description", "")) > 60:
            desc += "..."
        rel_path = skill["rel_path"]
        table.add_row(name, keywords_str, desc, rel_path)

    console.print(table)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="🧠 Skills Loader CLI (OpenCode-inspired)"
    )
    parser.add_argument(
        "--json", action="store_true", help="Output JSON instead of table"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list")
    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("query", nargs="?", default="", help="Search query")
    load_parser = subparsers.add_parser("load")
    load_parser.add_argument("name", help="Skill name or stem")

    args = parser.parse_args()

    stats, skills = get_all_skills()
    console = Console()

    if args.command == "list":
        if args.json:
            output = {"stats": stats, "skills": skills}
            print(json.dumps(output, indent=2, default=str))
        else:
            print_dashboard(stats, skills, console)
    elif args.command == "search":
        if not args.query:
            console.print("[red]Error: query required for search[/red]")
            return 1
        query = args.query.lower()
        filtered = [
            s
            for s in skills
            if (
                query in s.get("name", "").lower()
                or any(query in str(k).lower() for k in s.get("keywords", []))
                or query in s.get("description", "").lower()
            )
        ]
        search_stats = stats.copy()
        search_stats["found"] = len(filtered)
        if args.json:
            print(
                json.dumps(
                    {"stats": search_stats, "skills": filtered}, indent=2, default=str
                )
            )
        else:
            console.print(
                f"[bold yellow]🔍 Search '{args.query}': {len(filtered)} results[/bold yellow]\n"
            )
            print_dashboard(search_stats, filtered, console)
    elif args.command == "load":
        matches = [
            s
            for s in skills
            if args.name.lower() in s.get("name", "").lower()
            or args.name.lower() in s["file_path"].stem.lower()
        ]
        if not matches:
            console.print(f"[red]❌ Skill not found: {args.name}[/red]")
            console.print("[dim]Use 'grok-skills list' to browse.[/dim]")
            return 1
        if len(matches) > 1:
            console.print("[yellow]⚠️ Multiple matches:[/yellow]")
            for s in matches:
                console.print(
                    f"  • {s.get('name', s['file_path'].name)} ({s['rel_path']})"
                )
            console.print("[dim]Use more specific name.[/dim]")
            return 1
        skill = matches[0]
        if args.json:
            print(json.dumps(skill, indent=2, default=str))
        else:
            console.print(f"[bold cyan]{skill.get('name', 'Skill')}[/bold cyan]")
            console.print(
                f"[dim]Keywords: {', '.join(skill.get('keywords', []))}[/dim]"
            )
            console.print()
            console.print(Markdown(skill["full_content"]))
            console.print(f"\n[blue]📄 {skill['rel_path']} [/blue]")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
