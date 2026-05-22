---
name: whoami
description: Build an Agent-callable KYC knowledge base through conversation. Use when the user wants to capture preferences, values, goals, habits, social style, or decision patterns.
version: 1.0.0
---

## Core

- Each dimension file becomes Agent context
- `INDEX.md` routes tasks to the right files
- I learn myself. I acknowledge myself. I understand myself. I am myself.

## Workflow

1. Start broad. Ask about life, not just work.
2. Detect stable signals from conversation (traits, preferences, goals, rules, habits, social patterns).
3. For each potential dimension, run a proposal gate:
   - Signal observed: what I heard
   - Suggested dimension: file name + why it helps execution
   - Ask user to confirm before creating the file
4. Explore with options for factual questions and open input for reflective ones.
5. Draft each confirmed dimension as:

```markdown
# [DIMENSION_NAME]

> Optional one-line summary

## Theme

- user's exact words
```

Show the draft, confirm it, then save it. 6. Build `INDEX.md` dynamically with only confirmed files from this conversation.

## Recovery

- skip → skip
- whatever/either → recommend one, confirm fast
- partial capture → save and stop
- rename → rename before saving and update `INDEX.md`

## Completion

KYC is ready when:

- All created files were explicitly confirmed by the user
- Each file contains enough signal to support at least one real task decision
- `INDEX.md` lists only confirmed files and can guide retrieval
- No forced dimensions are added just to satisfy a template

## Incremental

1. Read existing files and `INDEX.md`
2. Ask what changed and what should stay untouched
3. Propose candidate dimensions only when new signals appear
4. Create/update files only after explicit user confirmation
5. Update `INDEX.md` to reflect confirmed additions/removals
6. Never auto-create missing dimensions for completeness

## Notes

- Keep it conversational
- Preserve the user's voice
- Prefer depth over breadth: fewer accurate dimensions beat many shallow ones
