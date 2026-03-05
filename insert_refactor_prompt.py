import re

with open('agent.py', 'r') as f:
    content = f.read()

with open('refactor_prompt_insert.txt', 'r') as f:
    insert = f.read()

pattern = r'- git_pull\\\\(confirm=\\\\"yes\\\\"\\\\): Pull from origin'
match = re.search(pattern, content)
if match:
    insert_pos = match.end()
    new_content = content[:insert_pos] + ' ' + insert + content[insert_pos:]
    with open('agent.py', 'w') as f:
        f.write(new_content)
    print('Prompt updated')
else:
    print('No match')