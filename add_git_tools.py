import re
import subprocess
import json
from pathlib import Path

with open('agent.py', 'r') as f:
    content = f.read()

# Find the position after web_search def, before run
match = re.search(r'def web_search\\(self,[^:]*:\\n.*?\\n\\n(?=  def run\\(', re.DOTALL | re.MULTILINE)
if match:
    insert_pos = f.tell()  # no, use content
    # Better use lines
lines = content.splitlines(True)

i = 0
for j in range(len(lines)):
    if 'def web_search(self' in lines[j]:
        i = j
    if i > 0 and 'def run(self' in lines[j]:
        # insert before j
        indent = '    '
        git_status_code = [
            f'{indent}def git_status(self) -> str:',
            f'{indent}    try:',
            f'{indent}        r = subprocess.run(',
            f'{indent}            [\\'git\\', \\'status\\', \\'--porcelain=v1\\'],',
            f'{indent}            cwd=str(self.target_dir),',
            f'{indent}            capture_output=True,',
            f'{indent}            text=True,',
            f'{indent}            timeout=10,',
            f'{indent}        )',
            f'{indent}        files = []',
            f'{indent}        if r.returncode == 0:',
            f'{indent}            for line in r.stdout.strip().splitlines():',
            f'{indent}                if line.strip():',
            f'{indent}                    parts = line.split(None, 1)',
            f'{indent}                    status = parts[0]',
            f'{indent}                    filename = parts[1] if len(parts) > 1 else \\'\\'',
            f'{indent}                    files.append({{\\'filename\\': filename, \\'status\\': status}})',
            f'{indent}        return json.dumps({{\\'files\\': files}})',
            f'{indent}    except Exception as e:',
            f'{indent}        return json.dumps({{\\'error\\': str(e)}})',
            '',
        ]
        # similar for others, but to start with one
        lines[j:j] = git_status_code
        break

with open('agent.py', 'w') as f:
    f.write(''.join(lines))

print('Added git_status')