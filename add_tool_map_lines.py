import re

with open('agent.py', 'r') as f:
    content = f.read()

with open('git_tool_map_add.txt', 'r') as f:
    insert = f.read()

pattern = r'self\\.tool_map = tool_map or default_tool_map'
match = re.search(pattern, content)
if match:
    insert_pos = match.start()
    new_content = content[:insert_pos] + insert + '\\n' + content[insert_pos:]
    with open('agent.py', 'w') as f:
        f.write(new_content)
    print('Tool map lines added')
else:
    print('self.tool_map line not found')