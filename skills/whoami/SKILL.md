---
name: whoami
description: Build an Agent-callable KYC knowledge base through conversation; dimensions emerge from signals and are created only after user confirmation.
version: 1.0.0
---

> [MANDATORY] Never create dimensions for "completeness". Dimensions must come from stable conversation signals and explicit user confirmation.

## Core

- Each dimension file is callable context for the Agent
- `INDEX.md` routes retrieval and includes only confirmed dimensions
- Goal: execution sufficiency, not template completeness

## Workflow

1. Start broad, then go deep into key dimensions.
2. Detect stable signals: traits, preferences, goals, principles, habits, social patterns, etc.
3. Run the Proposal Gate for each candidate dimension:
   - What signal was observed
   - Suggested dimension filename
   - Why this dimension improves task execution
   - Ask user confirmation before creation
4. Interview style: use "options + free input" for factual prompts, open input for reflective prompts.
5. Draft, confirm, then write.
6. Build `INDEX.md` dynamically (confirmed dimensions only).

## Dimension Draft Template

```markdown
# [DIMENSION_NAME]

> Optional one-line summary

## Theme

- user's exact words
```

## Completion

KYC is complete when:

- All created files are explicitly confirmed by the user
- Each file supports at least one real task decision
- `INDEX.md` can guide retrieval and execution
- No forced dimensions were added to satisfy a template

## Incremental Update

1. Read existing files and `INDEX.md`
2. Confirm what should change and what should remain untouched
3. Propose new dimensions only when new stable signals appear
4. Create/update only after explicit user confirmation
5. Sync `INDEX.md` for additions/removals
6. Never auto-create missing dimensions for completeness

## Notes

- Keep the conversation natural
- Preserve the user's original voice
- Prefer depth over breadth: fewer accurate dimensions beat many shallow ones
