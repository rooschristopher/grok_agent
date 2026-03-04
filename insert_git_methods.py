import re

with open('agent.py', 'r') as f:
    content = f.read()

with open('agent_git_methods_insert.txt', 'r') as f:
    methods = f.read()

# Find the start of def run, including possible whitespace before
pattern = r'\n\s*def run\(self, goal: str, max_steps: int = 200\) -> None:'
match = re.search(pattern, content)
if match:
    insert_pos = match.start()
    new_content = content[:insert_pos] + '\n' + methods + content[insert_pos:]
    with open('agent.py', 'w') as f:
        f.write(new_content)
    print('Methods inserted successfully')
else:
    print('Run method not found')
    print(repr(pattern))
    print('Possible matches:')
    for m in re.finditer(r'def run', content):
        print(content[m.start()-10:m.end()+50])