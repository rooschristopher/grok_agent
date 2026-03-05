import re

with open('agent.py', 'r') as f:
    content = f.read()

with open('debug_tools_insert.txt', 'r') as f:
    insert = f.read()

pattern = r'(tool\\s*\\(\\s*name="git_pull",.*?\\)\\s*),\\s*\\]'
match = re.search(pattern, content, re.DOTALL)
if match:
    insert_pos = match.end(1)
    new_content = content[:insert_pos] + insert + content[insert_pos:]
    with open('agent.py', 'w') as f:
        f.write(new_content)
    print('Debug tool schema inserted successfully')
else:
    print('No match for pattern:', repr(pattern))
    git_pull_pos = content.find('git_pull')
    print('Snippet:', repr(content[max(0,git_pull_pos-100):git_pull_pos+500]))