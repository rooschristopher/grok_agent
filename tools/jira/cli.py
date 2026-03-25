#!/usr/bin/env python3
import argparse
import os
import sys
from collections import Counter
from typing import Any

try:
    from jira import JIRA
except ImportError:
    print(
        "Error: 'jira' package not installed. Run 'uv add jira' or 'pip install jira'",
        file=sys.stderr,
    )
    sys.exit(1)


def connect() -> Any:
    server = os.getenv("JIRA_SERVER", "https://zeamster.atlassian.net")
    email = os.getenv("JIRA_EMAIL", "chris.roos@fortispay.com")
    api_key = os.getenv("JIRA_API_KEY")

    if not api_key:
        print("Error: JIRA_API_KEY environment variable is not set.", file=sys.stderr)
        print(
            "Create an API token at https://id.atlassian.net/manage-profile/security/api-tokens",
            file=sys.stderr,
        )
        sys.exit(1)

    return JIRA(server=server, basic_auth=(email, api_key))


def _issue_to_dict(
    issue: Any, include_body: bool = False, include_comments: bool = False
) -> dict[str, Any]:
    fields = getattr(issue, "fields", None)
    parent_key = getattr(getattr(fields, "parent", None), "key", None)

    data: dict[str, Any] = {
        "key": getattr(issue, "key", ""),
        "summary": getattr(fields, "summary", ""),
        "status": getattr(getattr(fields, "status", None), "name", ""),
        "project": getattr(getattr(fields, "project", None), "key", ""),
        "parent": parent_key or "",
        "updated": getattr(fields, "updated", ""),
        "created": getattr(fields, "created", ""),
        "url": f"{os.getenv('JIRA_SERVER', 'https://zeamster.atlassian.net')}/browse/{getattr(issue, 'key', '')}",
        "assignee": getattr(getattr(fields, "assignee", None), "displayName", ""),
        "reporter": getattr(getattr(fields, "reporter", None), "displayName", ""),
        "priority": getattr(getattr(fields, "priority", None), "name", ""),
        "issuetype": getattr(getattr(fields, "issuetype", None), "name", ""),
    }

    if include_body:
        data["description"] = getattr(fields, "description", "") or ""

    if include_comments:
        comments_container = getattr(fields, "comment", None)
        comments_list = (
            getattr(comments_container, "comments", []) if comments_container else []
        )
        serialized_comments: list[dict[str, str]] = []
        for c in comments_list:
            serialized_comments.append(
                {
                    "author": getattr(getattr(c, "author", None), "displayName", ""),
                    "created": getattr(c, "created", ""),
                    "updated": getattr(c, "updated", ""),
                    "body": getattr(c, "body", ""),
                }
            )
        data["comments"] = serialized_comments

    return data


status_emojis: dict[str, str] = {
    "To Do": "👀",
    "In Progress": "🔄",
    "Review": "📝",
    "In Review": "📝",
    "Done": "📦",
    "Resolved": "✅",
    "Blocked": "⛔",
    "On Hold": "⏸️",
    "Closed": "🔒",
    "Cancelled": "❌",
}

priority_emojis: dict[str, str] = {
    "Highest": "🔥🔥",
    "High": "🔥",
    "Medium": "⚡",
    "Low": "📋",
    "Lowest": "📌",
}

SAMPLE_TICKETS: list[dict[str, Any]] = [
    {
        "key": "PROJ-101",
        "summary": "Implement user authentication feature with OAuth2 and JWT tokens for secure API access",
        "status": "In Progress",
        "priority": "High",
        "updated": "2024-03-20T14:30:00.000+0000",
        "created": "2024-03-10T09:00:00.000+0000",
        "reporter": "Alice Johnson",
        "url": "https://zeamster.atlassian.net/browse/PROJ-101",
        "project": "PROJ",
        "assignee": "Dev Team",
        "issuetype": "Story",
        "description": "Develop a robust authentication system supporting OAuth2 flows. Include token refresh logic and security best practices.",
        "comments": [
            {
                "author": "Bob Smith",
                "updated": "2024-03-19T16:00:00",
                "body": "Working on OAuth integration.",
            },
            {
                "author": "Alice Johnson",
                "updated": "2024-03-20T10:00:00",
                "body": "Please add unit tests.",
            },
        ],
    },
    {
        "key": "PROJ-102",
        "summary": "Fix database connection timeout issues during peak hours - optimize pooling",
        "status": "To Do",
        "priority": "Highest",
        "updated": "2024-03-21T09:15:00.000+0000",
        "created": "2024-03-15T12:00:00.000+0000",
        "reporter": "Charlie Brown",
        "url": "https://zeamster.atlassian.net/browse/PROJ-102",
        "project": "PROJ",
        "assignee": "",
        "issuetype": "Bug",
    },
    {
        "key": "PROJ-103",
        "summary": "Update UI components to use new design system v2.0",
        "status": "Done",
        "priority": "Medium",
        "updated": "2024-03-18T16:45:00.000+0000",
        "created": "2024-03-05T14:30:00.000+0000",
        "reporter": "Alice Johnson",
        "url": "https://zeamster.atlassian.net/browse/PROJ-103",
        "project": "PROJ",
        "assignee": "Bob Smith",
        "issuetype": "Task",
    },
    {
        "key": "TEAM-45",
        "summary": "Review and merge PR #456 into main branch after QA approval",
        "status": "Review",
        "priority": "Low",
        "updated": "2024-03-21T11:20:00.000+0000",
        "created": "2024-03-19T15:00:00.000+0000",
        "reporter": "Dana Wilson",
        "url": "https://zeamster.atlassian.net/browse/TEAM-45",
        "project": "TEAM",
        "assignee": "Current User",
        "issuetype": "Sub-task",
    },
]


def status_stats_table(tickets: list[dict[str, Any]]) -> str:
    counts = Counter(t["status"] for t in tickets)
    lines = ["| Status | Count |\n| --- | ---: |\n"]
    for status, count in sorted(counts.items(), key=lambda x: -x[1]):
        emoji = status_emojis.get(status, "❓")
        lines.append(f"| {emoji} **{status}** | {count} |\n")
    return "".join(lines)


def priority_stats_table(tickets: list[dict[str, Any]]) -> str:
    counts = Counter(t.get("priority", "None") for t in tickets)
    lines = ["| Priority | Count |\n| --- | ---: |\n"]
    for prio, count in sorted(counts.items(), key=lambda x: -x[1]):
        emoji = priority_emojis.get(prio, "")
        cell = f"{emoji} **{prio}**" if emoji or prio != "None" else "**None**"
        lines.append(f"| {cell} | {count} |\n")
    return "".join(lines)


def project_stats_table(tickets: list[dict[str, Any]]) -> str:
    counts = Counter(t["project"] for t in tickets)
    lines = ["| Project | Count |\n| --- | ---: |\n"]
    for proj, count in sorted(counts.items(), key=lambda x: -x[1]):
        lines.append(f"| 📁 **{proj}** | {count} |\n")
    return "".join(lines)


def main_table(tickets: list[dict[str, Any]]) -> str:
    lines = [
        "| Key | Status | Priority | Summary | **Updated** | Reporter | Open |\n| --- | --- | --- | --- | --- | --- | --- |\n"
    ]
    for t in tickets:
        key_link = f"[{t['key']}]({t['url']})"
        st_emoji = status_emojis.get(t["status"], "❓")
        status_cell = f"{st_emoji} {t['status']}"
        prio = t.get("priority", "None")
        p_emoji = priority_emojis.get(prio, "")
        prio_cell = f"{p_emoji} {prio}" if p_emoji or prio != "None" else "None"
        summary = t["summary"][:60] + "..." if len(t["summary"]) > 60 else t["summary"]
        updated = t["updated"][:10]
        reporter = t.get("reporter", "N/A")
        open_cell = f"[🖥️]({t['url']})"
        lines.append(
            f"| {key_link} | {status_cell} | {prio_cell} | {summary} | **{updated}** | {reporter} | {open_cell} |\n"
        )
    return "".join(lines)


def format_list(tickets: list[dict[str, Any]], query: str) -> str:
    total = len(tickets)
    header = f"# {query}\n\n**Total: {total}** • *Sorted by updated DESC*\n\n"
    stats = "## 📊 Stats\n\n"
    stats += status_stats_table(tickets) + "\n\n"
    stats += priority_stats_table(tickets) + "\n\n"
    stats += project_stats_table(tickets) + "\n\n"
    main = "## 📋 Main Table\n\n" + main_table(tickets)
    footer = """
## 🚀 Next Actions
- View details: `python tools/jira/cli.py get KEY`
- Include done: `python tools/jira/cli.py list-my --include-done`
- Custom search: `python tools/jira/cli.py search --jql "project=PROJ"`
- Open [Your Work Dashboard](https://zeamster.atlassian.net/jira/your-work)
"""
    return header + stats + main + footer


def format_single(ticket: dict[str, Any]) -> str:
    key = ticket["key"]
    summary = ticket["summary"]
    url = ticket["url"]
    header = (
        f"# {key}: **{summary}**\n\n🖥️ [Open]({url}) | ✏️ [Edit]({url}?mode=edit)\n\n"
    )
    facts = "## 📊 Key Facts\n\n"
    facts_table = "| Field | Value |\n| --- | --- |\n"
    facts_table += f"| **Key** | [{key}]({url}) |\n"
    facts_table += f"| **Status** | {status_emojis.get(ticket.get('status', ''), '❓')} **{ticket['status']}** |\n"
    prio = ticket.get("priority", "N/A")
    p_emoji_s = priority_emojis.get(prio, "")
    facts_table += f"| **Priority** | {p_emoji_s} **{prio}** |\n"
    facts_table += f"| **Assignee** | **{ticket.get('assignee', 'Unassigned')}** |\n"
    facts_table += f"| **Reporter** | **{ticket.get('reporter', 'N/A')}** |\n"
    facts_table += f"| **Updated** | **{ticket['updated'][:10]}** |\n"
    facts_table += f"| **Created** | **{ticket.get('created', '')[:10]}** |\n"
    facts_table += f"| **Project** | 📁 **{ticket['project']}** |\n"
    facts_table += f"| **Type** | **{ticket.get('issuetype', '')}** |\n"
    facts += facts_table + "\n\n"
    desc = ticket.get("description", "")
    desc_sec = (
        f"## 📄 Description\n\n{desc}\n\n"
        if desc
        else "## 📄 Description\n\n_No description provided._\n\n"
    )
    comments = ticket.get("comments", [])
    comm_sec = "## 💬 Recent Comments\n\n"
    if not comments:
        comm_sec += "_No comments._\n"
    else:
        for c in comments:
            author = c.get("author", "Unknown")
            c_updated = c.get("updated", "")[:10]
            body = c.get("body", "")
            comm_sec += f"**{author}** *({c_updated})*\n\n{body}\n\n---\n\n"
    footer = f"""
## 🚀 Next Actions
- Add comment or transition in [Jira]({url})
- `python tools/jira/cli.py get {key} --include-comments` (if supported)
"""
    return header + facts + desc_sec + comm_sec + footer


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="""🛠️ Jira CLI Dashboard

Rich Markdown dashboard for Jira tickets.""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python tools/jira/cli.py list-my
  python tools/jira/cli.py list-my --sample
  python tools/jira/cli.py search --jql "assignee = currentUser() AND status = 'To Do'"
  python tools/jira/cli.py get PROJ-101 --sample
""",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list-my", help="List assigned tickets")
    list_parser.add_argument(
        "--include-done", action="store_true", help="Include Done/Resolved"
    )
    list_parser.add_argument(
        "--max-results", type=int, default=50, help="Max results (default 50)"
    )
    list_parser.add_argument(
        "--sample", action="store_true", help="Test with sample data"
    )

    search_parser = subparsers.add_parser("search", help="Search with JQL")
    search_parser.add_argument("--jql", required=True, help="JQL query")
    search_parser.add_argument("--max-results", type=int, default=50)
    search_parser.add_argument("--sample", action="store_true")

    get_parser = subparsers.add_parser("get", help="Get ticket details")
    get_parser.add_argument("key", help="Ticket key (e.g. PROJ-123)")
    get_parser.add_argument("--sample", action="store_true")
    get_parser.add_argument(
        "--include-comments", action="store_true", help="Include comments"
    )

    args = parser.parse_args()

    if args.sample:
        if args.command == "get":
            sample_ticket = next(
                (t for t in SAMPLE_TICKETS if t["key"] == args.key), None
            )
            if not sample_ticket:
                print(
                    f"Sample data not found for {args.key}. Available: {[t['key'] for t in SAMPLE_TICKETS]}",
                    file=sys.stderr,
                )
                sys.exit(1)
            print(format_single(sample_ticket))
        else:
            query = (
                "My Sample Tickets"
                if args.command == "list-my"
                else f"Sample Search: {args.jql}"
            )
            print(format_list(SAMPLE_TICKETS, query))
        sys.exit(0)

    # Real Jira connection
    try:
        jira_client = connect()
    except Exception as e:
        print(f"❌ Jira connection failed: {e}", file=sys.stderr)
        print("Check JIRA_SERVER, JIRA_EMAIL, JIRA_API_KEY env vars.", file=sys.stderr)
        sys.exit(1)

    try:
        if args.command == "list-my":
            status_filter = "" if args.include_done else "AND statusCategory != Done"
            jql = f"assignee = currentUser() {status_filter} ORDER BY updated DESC"
            issues = jira_client.search_issues(jql, maxResults=args.max_results)
            tickets = [_issue_to_dict(issue) for issue in issues]
            query = f"My Tickets{' (incl. Done)' if args.include_done else ''}"
            print(format_list(tickets, query))
        elif args.command == "search":
            issues = jira_client.search_issues(args.jql, maxResults=args.max_results)
            tickets = [_issue_to_dict(issue) for issue in issues]
            print(format_list(tickets, f"Search: {args.jql}"))
        elif args.command == "get":
            issue = jira_client.issue(args.key)
            inc_comments = args.include_comments
            ticket = _issue_to_dict(
                issue, include_body=True, include_comments=inc_comments
            )
            print(format_single(ticket))
    except Exception as e:
        print(f"❌ Query failed: {e}", file=sys.stderr)
        sys.exit(1)
