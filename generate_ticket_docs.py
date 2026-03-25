import json
import os
import re
import subprocess

# Fetch fresh JSON
result = subprocess.run(["python", "tools/jira/list_my_tickets.py"], capture_output=True, text=True)
if result.returncode != 0:
    print("Error fetching tickets:", result.stderr)
    exit(1)

json_str = result.stdout
tickets = json.loads(json_str)
print(f"Fetched {len(tickets)} tickets")

# Mappings
status_emojis = {
    "In Progress": "🔄",
    "Backlog": "📦",
    "To DO": "👀",
    "Approved": "✅",
    "In Review": "📝",
    "Blocked": "⛔",
    "On Hold": "⏸️",
}

priority_emojis = {
    "High": "🔥",
    "Medium": "⚡",
    "Low": "📋",
    "Not Set": "",
}

def sanitize_status(status):
    sanitized = re.sub(r'\s+', '_', status)
    sanitized = sanitized.replace('/', '-')
    sanitized = re.sub(r'[^\w\-_]', '', sanitized)
    return sanitized

created_files = []
base_dir = "/home/croos/work/fortis/docs/tickets"

for ticket in tickets:
    status = ticket["status"]
    sanitized_status = sanitize_status(status)
    dir_path = os.path.join(base_dir, sanitized_status)
    os.makedirs(dir_path, exist_ok=True)
    key = ticket["key"]
    file_path = os.path.join(dir_path, f"{key}.md")
    summary = ticket["summary"]
    updated = ticket["updated"]
    reporter = ticket["reporter"]
    url = ticket["url"]
    priority = ticket["priority"]
    status_emoji = status_emojis.get(status, '')
    priority_emoji = priority_emojis.get(priority, '')
    date_synced = subprocess.check_output(["date"]).decode().strip()
    content = f"""# {key}

## Summary
{summary}

## Progress Log
No documented progress yet.

**Next steps:** Research git logs in relevant repos (e.g. `git log --grep="{key}"`), chats/, prior agent convos.

## Jira Details
- **Status**: {status} {status_emoji}
- **Priority**: {priority} {priority_emoji}
- **Updated**: {updated}
- **Reporter**: {reporter}
- **URL**: {url}

Last synced: {date_synced}
"""
    with open(file_path, 'w') as f:
        f.write(content)
    created_files.append(file_path)
    print(f"Created: {file_path}")

print("\nCreated files:")
for f in created_files:
    print(f)