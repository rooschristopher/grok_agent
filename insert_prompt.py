import re

with open('agent.py', 'r') as f:
    content = f.read()

with open('git_prompt_insert.txt', 'r') as f:
    insert = f.read()

pattern = r'- web_search\\(query, num_results=5\\): Google search'
match = re.search(pattern, content)
if match:
    insert_pos = match.end()
    new_content = content[:insert_pos] + '\\n' + insert + content[insert_pos:]
    with open('agent.py', 'w') as f:
        f.write(new_content)
    print('Prompt updated')
else:
    print('No match')