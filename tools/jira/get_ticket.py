#!/usr/bin/env python3
import argparse
import json
import os
import sys
from typing import Any

try:
    from jira import JIRA  # type: ignore
except ImportError:
    print(
        "Error: 'jira' package not installed. Run 'pip install jira'", file=sys.stderr
    )
    sys.exit(1)


def connect() -> Any:
    server = os.getenv("JIRA_SERVER", "https://zeamster.atlassian.net")
    email = os.getenv("JIRA_EMAIL", "chris.roos@fortispay.com")
    api_key = os.getenv("JIRA_API_KEY")

    if not api_key:
        print("Error: JIRA_API_KEY environment variable is not set.", file=sys.stderr)
        print(
            "Create an API token at https://id.atlassian.com/manage-profile/security/api-tokens",
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
        serialized_comments: List[dict[str, str]] = []
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


def get_ticket(
    jira_client: Any,
    key: str,
    include_body: bool = True,
    include_comments: bool = False,
) -> dict[str, Any]:
    issue = jira_client.issue(key)
    return _issue_to_dict(
        issue, include_body=include_body, include_comments=include_comments
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get a single Jira ticket")
    parser.add_argument("--key", required=True, help="Issue key, e.g., ABC-123")
    parser.add_argument(
        "--include-body",
        action="store_true",
        default=True,
        help="Include description (default: yes)",
    )
    parser.add_argument(
        "--include-comments", action="store_true", help="Include comments"
    )
    args = parser.parse_args()

    j = connect()
    ticket = get_ticket(j, args.key, args.include_body, args.include_comments)
    print(json.dumps(ticket, default=str, indent=2))
