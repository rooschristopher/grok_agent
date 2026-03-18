# Grok Agent Skills Directory

Inspired by [OpenCode Skills](https://opencode.ai/docs/skills/) and [Vercel Skills](https://github.com/vercel-labs/skills).

## Format
Skills are Markdown files named `name.SKILL.md` (e.g., `tdd.SKILL.md`).

**Required YAML Frontmatter:**
```yaml
---
name: Skill Name
description: Brief description.
keywords: [tag1, tag2]  # For search/discovery
applies_to: [coding, testing]  # Optional categories
---
```

**Body:** Markdown instructions/prompts for the agent to follow when using this skill.

## Discovery & Usage
- List: `ls .grok_agent/skills/*.SKILL.md`
- Load: Read the file, parse frontmatter, inject body into context.
- Example: Agent tools can search keywords and apply relevant skills.

## Examples
See `tdd.SKILL.md`, `refactor.SKILL.md`.

Drop new skills here—agent will discover them! 🚀