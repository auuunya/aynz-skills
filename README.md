# aynz-skills

A curated open-source skill collection for AI agents.

## Included Skills

- `skills/whoami` — build an Agent-callable KYC knowledge base via conversation
- `skills/stage-manager` — stage planning, execution tracking, ADR logging, and archive gating
- `skills/tdd-spec-loop` — turn requirements into an AI-operable TDD feedback environment

## Structure

```text
aynz-skills/
├── skills/
│   ├── whoami/
│   ├── stage-manager/
│   └── tdd-spec-loop/
└── README.md
```

## Conventions

- Each skill entrypoint is `SKILL.md`
- Frontmatter should include: `name`, `description`, `version`
- Optional `SKILL.override.md` for repo-level constraints
