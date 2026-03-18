# 🛠️ Permanent Agent Instructions (Updated 2026-03-15)

## 🎨 Jira Tools: CLI Dashboard Format (MANDATORY)
For `jira_list_my_tickets`, `jira_search_tickets`, `jira_get_ticket`:

1. **Header**: &quot;Jira [Query Summary] - Total: X tickets (sorted by updated desc)&quot;

2. **📊 Stats Overview** (group by status/project/priority):

   | Group          | Count | Emoji |
   |----------------|-------|-------|
   | In Progress    | 5     | 🔄   |
   | Done           | 10    | ✅   |
   | High Priority  | 3     | 🔥   |

3. **📋 Tickets Table**:

   | Key                  | Status       | Priority | Summary (trunc 50)     | Updated  | Reporter | Actions          |
   |----------------------|--------------|----------|------------------------|----------|----------|------------------|
   | [PROJ-123](link)     | 🔄 In Progress | 🔥 High | Fix critical bug... | **15 Mar** | @alice  | [View](link)     |
   | PROJ-456             | ✅ Done      | ⚡ Med  | Update docs...        | **14 Mar** | @bob    | [View](link)     |

4. **Single Ticket View**:

   **Key Facts:**

   | Field    | Value              |
   |----------|--------------------|
   | Status   | 🔄 In Progress     |
   | Priority | 🔥 High            |
   | Assignee | @bob               |

   **Description:** [formatted md]

   **Comments:** 
   - @alice: Good point 🔄 (15 Mar)

5. **Emojis Guide**:
   - Status: 🔄(In Progress) 👀(To Do) 📦(In Review) ✅(Done) ⛔(Blocked) 📝(New) ⏸️(On Hold)
   - Priority: 🔥(High) ⚡(Medium) 📋(Low)

**ALWAYS**: Transform raw JSON to this beautified Markdown. NO plain lists!

## 🔗 GitHub CLI: Dashboard Format
Fetch via `gh` CLI e.g. `gh issue list --assignee @me --json title,number,state,updatedAt,repository,url,labels`

**Header**: &quot;GitHub My Issues/PRs - Total: X (updated desc)&quot;

**📊 Stats** (by repo/state):

| Repo/State   | Count |
|--------------|-------|
| grok_agent/Open 🟢  | 2    |
| grok_agent/Closed 🔴| 5    |

**📋 Items Table**:

| Repo       | Title [#ID](url)             | State | Updated  | Labels     |
|------------|------------------------------|-------|----------|------------|
| grok_agent | Fix CLI tables 🐛 [#19](link)| 🟢 Open | **15 Mar**| feat,cli 📋|
| grok_agent | Add rich tables [#20]        | 🔴 Closed| **14 Mar**| enhancement|

**Pro Tip**: `gh browse #19` to open.

## 🚀 General Rules
- **Concise + Helpful**: End w/ prompts: &quot;Next: approve PR? `gh pr merge`&quot;
- **Fresh Data**: Always re-fetch w/ `gh issue list ...`
- **CLI Vibe**: Emojis, tables, **bold** updated, clickable links.
- **Rich-Inspired**: Mimic `rich` tables in Markdown.

**Persist Changes**: `git commit -m &quot;docs: update agent instructions&quot; &amp;&amp; git push` ## 🧠 Skills System (OpenCode-Inspired)

**Discover & Apply Skills Dynamically:**

1. **List**: `list_dir(".grok_agent/skills")` – See `*.SKILL.md` files.

2. **Search**: For task keywords, `run_shell('grep -l -i "tdd test" .grok_agent/skills/*.SKILL.md')` or manually check.

3. **Load**: `read_file("path/to/skill.SKILL.md")` → Parse YAML frontmatter (name, desc, keywords), **apply body instructions** to current task.

**Examples**:
- **TDD**: Use `tdd.SKILL.md` for red-green-refactor.
- **Git**: `git-workflow.SKILL.md` before commits.

**Always**: When relevant (e.g., "implement feature" → check TDD), load & follow 1-2 top skills. Prefix reasoning: "**Using Skill: [Name]**".

Add new skills to dir—auto-discoverable! 🚀