import re

with open('agent.py', 'r') as f:
    content = f.read()

with open('refactor_tool_schema_insert.txt', 'r') as f:
    insert = f.read()

pattern = r'tool\\(\\s*name="git_pull" [ ^`]*? \\),'
match = re.search(pattern, content, re.DOTALL)
if match:
    insert_pos = match.end()
    new_content = content[:insert_pos] + '\\n' + insert + content[insert_pos:]
    with open('agent.py', 'w') as f:
        f.write(new_content)
    print('Tool schema inserted')
else:
    print('No match')