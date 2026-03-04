import re

with open('agent.py', 'r') as f:
    content = f.read()

with open('git_tool_map_insert.txt', 'r') as f:
    insert = f.read()

pattern = r'\"web_search\": self\\.web_search,'
match = re.search(pattern, content)
if match:
    insert_pos = match.end()
    new_content = content[:insert_pos] + '\\n' + insert + content[insert_pos:]
    with open('agent.py', 'w') as f:
        f.write(new_content)
    print('Tool map updated')
    print('Success')
else:
    print('No match')
    print(repr(pattern))