# 🛠️ Permanent Agent Instructions (Updated 2024-10-18)

## 🔒 Anti-Escaping & Validation Protocol (CRITICAL #1 PRIORITY)
**BEFORE any `write_file` for code/config (py/md/json):**

1. **Raw Output Only**:
   - Quotes: \" or \' — NEVER &quot;, &apos;.
   - XML/Special: < > & directly in content (tools parse raw).
   - Newlines: Actual line breaks, NO \\n literals in code strings.

2. **Mandatory Test Cycle** (use temp file):
   ```
   write_file("temp_validate.py", raw_content)
   run_shell("python -m py_compile temp_validate.py && ruff check --fix temp_validate.py")
   run_shell("pytest temp_validate.py -v || echo 'Syntax OK, manual test pass'")
   content = read_file("temp_validate.py")  # Re-read fixed
   assert ' &quot; ' not in content
   run_shell("rm temp_validate.py")
   ```
   For .md/JSON: ruff + grep no entities.

3. **Tool Calls**: Raw XML:
   ```
   <xai:function_call name="write_file">
   <parameter name="content">def hello(): print("world")