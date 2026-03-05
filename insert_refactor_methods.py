import re

with open('agent.py', 'r') as f:
    content = f.read()

with open('refactor_agent_method_insert.txt', 'r') as f:
    methods = f.read()

pattern = r'\\n\\s*def run\\(self, goal: str, max_steps: int = 200\\) -> None:'
match = re.search(pattern, content)
if match:
    insert_pos = match.start()
    new_content = content[:insert_pos] + '\\n' + methods + content[insert_pos:]
    with open('agent.py', 'w') as f:
        f.write(new_content)
    print('Methods inserted successfully')
else:
    print('Run method not found')