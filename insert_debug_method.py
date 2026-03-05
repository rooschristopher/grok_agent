import re

with open('agent.py', 'r') as f:
    content = f.read()

with open('debug_method_insert.txt', 'r') as f:
    insert = f.read()

pattern = r'def run\\(self, goal: str, max_steps: int = 200\\) -> None:'
match = re.search(pattern, content)
if match:
    insert_pos = match.start()
    new_content = content[:insert_pos] + insert + '\\n\\n' + content[insert_pos:]
    with open('agent.py', 'w') as f:
        f.write(new_content)
    print('Debug method inserted successfully')
else:
    print('No match for run method')
    print(repr(pattern))