import json
import subprocess
from collections import defaultdict


def get_repo_name(url):
    """Extract repo name from GitHub URL like https://github.com/owner/repo/issues/123"""
    parts = url.rstrip("/").split("/")
    return parts[4]


def format_date(date_str):
    return date_str[:10]


def get_repo_stats(data):
    repo_stats = defaultdict(lambda: {"open": 0, "closed": 0})
    for item in data:
        repo = get_repo_name(item["url"])
        state = item["state"].lower()
        repo_stats[repo][state] += 1
    total_open = sum(s["open"] for s in repo_stats.values())
    total_closed = sum(s["closed"] for s in repo_stats.values())
    return dict(repo_stats), total_open, total_closed


def build_stats_md(repo_stats, total_open, total_closed, pr_emoji=""):
    md = "## 📊 Stats\n\n"
    md += f"| Repo{pr_emoji} | 🟢 Open | 🔴 Closed |\n"
    md += "|-----------|---------|-----------|\n"
    for repo in sorted(repo_stats.keys()):
        o = repo_stats[repo]["open"]
        c = repo_stats[repo]["closed"]
        md += f"| {repo} | {o} | {c} |\n"
    md += f"\n**Total: 🟢 {total_open} | 🔴 {total_closed}**\n\n"
    return md


def build_table_md(data, header_emoji):
    md = f"## {header_emoji}\n\n"
    md += "| Repo | Title | State | Updated | Labels | [Open] |\n"
    md += "|------|-------|-------|---------|--------|--------|\n"
    for item in data:
        repo = get_repo_name(item["url"])
        title = item["title"][:60]
        if len(item["title"]) > 60:
            title += "..."
        url = item["url"]
        state = item["state"]
        state_emoji = "🟢" if state == "OPEN" else "🔴"
        updated = format_date(item["updatedAt"])
        labels = ", ".join(l["name"] for l in item["labels"]) if item["labels"] else "–"
        md += f"| {repo} | [{title}]({url}) | {state_emoji} | **{updated}** | {labels} | [Browse]({url}) |\n"
    return md


def run_gh_dashboard(cmd_base, title, emoji, count_desc):
    result = subprocess.run(cmd_base, capture_output=True, text=True)
    if result.returncode != 0:
        return f"# ❌ Error running gh: {result.stderr.strip()}\n"
    try:
        data = json.loads(result.stdout.strip()) if result.stdout.strip() else []
    except json.JSONDecodeError:
        return "# ❌ Invalid JSON from gh\n"
    if not data:
        return f"# {emoji} No items found\n"

    repo_stats, total_open, total_closed = get_repo_stats(data)
    stats_md = build_stats_md(
        repo_stats, total_open, total_closed, " 🔄" if "pr" in title.lower() else ""
    )
    table_md = build_table_md(data, f"{emoji}")
    return f"# {title}\n\n**{len(data)} {count_desc} (sorted by updated desc)**\n\n{stats_md}{table_md}"


def issues_dashboard():
    cmd = [
        "gh",
        "issue",
        "list",
        "--assignee",
        "@me",
        "--json",
        "url,title,state,updatedAt,labels",
        "--limit",
        "20",
    ]
    return run_gh_dashboard(cmd, "My GitHub Issues Dashboard", "🐛 Issues", "issues")


def prs_dashboard():
    cmd = [
        "gh",
        "pr",
        "list",
        "--assignee",
        "@me",
        "--json",
        "url,title,state,updatedAt,labels",
        "--limit",
        "20",
    ]
    return run_gh_dashboard(cmd, "My GitHub PRs Dashboard", "🔄 PRs", "PRs")


def full_dashboard():
    issues = issues_dashboard()
    prs = prs_dashboard()
    return f"{issues}\n\n---\n\n{prs}"


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="GitHub CLI Dashboard")
    parser.add_argument(
        "mode",
        nargs="?",
        default="full",
        choices=["issues", "prs", "full"],
        help="Dashboard mode",
    )
    args = parser.parse_args()
    func = {"issues": issues_dashboard, "prs": prs_dashboard, "full": full_dashboard}[
        args.mode
    ]
    print(func())
