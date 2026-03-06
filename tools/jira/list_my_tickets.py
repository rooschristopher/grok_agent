#!/usr/bin/env python3
import os
import sys
import json
import argparse
from typing import Any, Dict, List

try:
    from jira import JIRA  # type: ignore
except ImportError as e:
    print("Error: 'jira' package not installed. Run 'pip install jira'", file=sys.stderr)
    sys.exit(1)

def connect() -> Any:
    server = os.getenv("JIRA_SERVER", "https://zeamster.atlassian.net")
    email = os.getenv("JIRA_EMAIL", "chris.roos@fortispay.com")
    api_key = os.getenv("JIRA_API_KEY")

    if not api_key:
        print("Error: JIRA_API_KEY environment variable is not set.", file=sys.stderr)
        print("Create an API token at https://id.atlassian.com/manage-profile/security/api-tokens", file=sys.stderr)
        sys.exit(1)

    return JIRA(server=server, basic_auth=(email, api_key))


def _issue_to_dict(issue: Any, include_body: bool = False, include_comments: bool = False) -> Dict[str, Any]:
    fields = getattr(issue, "fields", None)
    parent_key = getattr(getattr(fields, "parent", None), "key", None)

    data: Dict[str, Any] = {
        "key": getattr(issue, "key", ""),
        "summary": getattr(fields, "summary", ""),
        "status": getattr(getattr(fields, "status", None), "name", ""),
        "project": getattr(getattr(fields, "project", None), "key", ""),
        "parent": parent_key or "",
        "updated": getattr(fields, "updated", ""),
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
        comments_list = getattr(comments_container, "comments", []) if comments_container else []
        serialized_comments: List[Dict[str, str]] = []
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


def list_my_tickets(
    jira_client: Any,
    include_done: bool = False,
    max_results: int = 200,
    include_body: bool = False,
    include_comments: bool = False,
) -> List[Dict[str, Any]]:
    status_filter = "" if include_done else "AND statusCategory != Done"
    jql = f"assignee = currentUser() {status_filter} ORDER BY updated DESC"

    issues = jira_client.search_issues(jql, maxResults=max_results)

    return [
        _issue_to_dict(issue, include_body=include_body, include_comments=include_comments)
        for issue in issues
    ]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="List Jira tickets assigned to you")
    parser.add_argument("--include-done", action="store_true", help="Include done tickets")
    parser.add_argument("--max-results", type=int, default=200, help="Max results (default: 200)")
    parser.add_argument("--include-body", action="store_true", help="Include issue descriptions")
    parser.add_argument("--include-comments", action="store_true", help="Include comments")
    args = parser.parse_args()

    j = connect()
    tickets = list_my_tickets(j, args.include_done, args.max_results, args.include_body, args.include_comments)
    print(json.dumps(tickets, default=str, indent=2))