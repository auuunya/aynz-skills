---
name: stage-manager
description: Stage planning, task decomposition, progress sync, ADR logging, backlog intake, session summary, and archive gating skill.
version: 1.0.0
---

> [MANDATORY] If `SKILL.override.md` exists, read it first. Its constraints override this file.
>
> [MANDATORY] All operations that write into `.stages/` or stage documents must run serially. Do not run `stage:init`, `stage:sync`, `stage:summary`, `stage:intake`, `stage:check`, `stage:switch`, `stage:done` concurrently; `sub_agent` is read-only by default.

## 0. Hard Rules

- Real entrypoint for `stage:*` is:

```text
python3 <skill-path>/scripts/stage.py <subcommand>
```

- Stable CLI entry is `scripts/stage.py`; `scripts/core/*.py` is internal. Do not modify `core/` unless explicitly requested.
- `.stages/` is runtime system assets; `.stage/` is delivery evidence. Do not mix them.
- Do not manually edit `.stages/STAGES.md`, `ADRS.md`, `BACKLOGS.md`, `STAGE_SESSIONS.md`.
- Use `TBD` / `null` / `[]` for unknowns. Do not fabricate.
- Use `--file <stage-file>` when operating on non-current stages; `bootstrap` has no `--file` semantics.

## 1. Three Shortest Paths

| Scenario | Action sequence |
| :--- | :--- |
| New project, no current stage | `stage:bootstrap` -> read `references/best_practice.md` -> `stage:init <name>` -> complete `## 1-6` -> `stage:validate` |
| Continue current stage | `stage:bootstrap` -> `stage:status` -> `stage:sync` / `stage:check` / `stage:intake` |
| Ready to archive | `stage:validate` -> `stage:summary --stage ...` -> verify DoD -> `stage:done` |

For new stage creation, "bootstrap -> read best_practice -> init" is a hard order, not a suggestion.
If an answer omits "read `references/best_practice.md`", treat it as incomplete; do not hide it under vague phrasing.

## 2. Command Mapping

| Semantic command | CLI subcommand | Purpose |
| :--- | :--- | :--- |
| `stage:bootstrap` | `bootstrap` | Load session snapshot, recent decisions, current stage, and backlog |
| `stage:init <name>` | `init <name>` | Initialize a stage and register index |
| `stage:sync "<msg>"` | `sync "<msg>"` | Incremental log; `[ADR]` prefix creates ADR stub and index |
| `stage:summary "<text>"` | `summary "<text>"` | Save session snapshot |
| `stage:summary --stage ...` | `summary --stage ...` | Write `## 9. Stage Summary` |
| `stage:intake "<keyword>"` | `intake "<keyword>"` | Claim tasks from backlog |
| `stage:status` | `status` | Inspect health, progress, recent decisions, and session summaries |
| `stage:validate` | `validate` | Validate stage document |
| `stage:check <ID>` | `check <ID>` | Toggle task/AC checklist |
| `stage:switch <file>` | `switch <file>` | Switch current stage pointer |
| `stage:done` | `done` | Close and archive; do not use `--force` without authorization |

## 3. Document & Process Rules

- Canonical template: `references/stage_template.md`
- Best practice: `references/best_practice.md`

### 3.1 Document Structure

- Keep all `@section:*` anchors, section numbering, and order.
- Update only impacted sections incrementally; avoid full rewrites.
- When adding the first real item, replace `- None` placeholder.

### 3.2 Schema Constraints

- Task lines and AC format must follow `references/stage_template.md`.
- Allowed `executor`: `agent` / `human` / `sub_agent`
- Allowed `verify_by`: `task_completion` / `evidence_review` / `metric_threshold` / `artifact_presence`
- Unknown `due`: use `YYYY-MM-DD` or `null`

### 3.3 Evidence

- Keep code/test evidence in original project paths.
- Put non-code evidence (reports/docs/logs/snapshots) under `.stage/`.
- `evidence` should prefer existing or confirmed-to-be-produced artifacts; use `TBD` if uncertain.
- Implementation stages must produce real code/config/test changes; logs/summaries/ADRs alone are not sufficient.

### 3.4 ADR

- Use `stage:sync "[ADR] <title>"` to create ADR stub and index.
- Only incrementally complete four fields in `## 8. Key Decisions (ADRs)`: background/motivation, alternatives, decision, impact/consequences.
- Do not manually edit `.stages/ADRS.md`.
- Keep `TBD` and ask user for missing info; do not fabricate.

### 3.5 Done Gate

Before `stage:done`, verify:

1. All `[P0]` tasks are complete
2. All checks in `## 5. Acceptance Criteria` are checked
3. New ideas from `## 3. Out of Scope` are migrated to backlog or future stages
4. Session snapshot and stage summary are completed, unless user explicitly allows minimal archive summary
5. Implementation stage has real evidence

If not satisfied, report missing items verbatim. Do not use `--force` without user authorization.

## 4. Output Requirements

- Logs must point to concrete modules/APIs/files/risks/ADRs; avoid vague statements.
- Session snapshot and stage summary are different actions:
  - Session snapshot: `stage:summary "<text>"`
  - Stage summary: `stage:summary --stage --name ... --goal ... --result ... --audit ... --debt ...`
- Planning stages may output docs/plans/audit artifacts.
- Implementation stages must land code/config/test/build artifacts.

### Minimal module-level log template

```text
<module/api/file> | change=<delta or current status> | evidence=<test/doc/path/ADR, use TBD if unknown> | next=<next concrete step> | risk=<none / specific risk>
```

- One log entry should describe one module topic; split cross-module updates.
- `next` must be immediately actionable.
- If there is no risk, write `none`.

## 5. Evaluation & Recovery

- Dry-run evaluation should at least cover: new stage creation, current-stage progress + ADR logging, archive gating, and single-writer constraints.

Common recovery actions:

- No current stage after `bootstrap`: `stage:init <name>`
- Need to operate another stage: append `--file <stage-file>` to write commands
- `validate` returns WARN only: continue, but resolve before `done`
- `done` rejected: fix docs/evidence first, then retry; no `--force` without authorization
