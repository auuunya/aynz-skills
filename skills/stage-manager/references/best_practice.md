# references/best_practice.md

> Best-practice supplement only. Field schema and placeholder formats are defined by `stage_template.md`.

## 1. Core Principles

- Isolation: failure in Stage N should not crash the whole system; add rollback/degrade plans when needed.
- Docs as code: maintain `stage-XXX.md` with the same rigor as code.
- Incremental updates: update impacted sections only; avoid full rewrites.
- Single writer: only one Agent may execute `stage:*` write commands at a time.
- Use consistent stage-status terms: `current stage`, `other stages`, `archived stages`.

## 2. Task Decomposition

Use INVEST:

- Independent: avoid cyclic dependencies
- Valuable: every task should produce visible value
- Estimatable: ideally within 1–2 days
- Small: easy to check off and roll back
- Testable: must be verifiable

Additional requirements:

- If decomposition or estimation is unclear, keep splitting.
- `acceptance` points to AC; do not mix `deliverables` with `evidence`.
- Keep `TASK-900` as the stage acceptance task.

## 3. Evidence

- Code evidence: keep original project paths, e.g., `src/...`, `tests/...`
- Non-code evidence: place under `.stage/`, e.g., `reports/`, `docs/`, `logs/`, `snapshots/`
- Every P0 task should have at least one readable evidence item
- Every AC should have at least one verifiable evidence reference
- For implementation stages, no code/test/config evidence means not done

## 4. Acceptance Criteria

- Prefer "action + result" statements; avoid vague phrases like "as expected" or "mostly done"
- `required_checks` should be verifiable checkpoints, e.g., `login_api_returns_token`
- Traceability ACs should cover one or more of log / ADR / summary

## 5. Multi-Agent Collaboration

- Multiple Agents may work in parallel on code, reports, or analysis
- Only one Agent may run `stage:init`, `stage:sync`, `stage:summary`, `stage:intake`, `stage:check`, `stage:switch`, `stage:done`
- `sub_agent` is read-only by default; hand results back to the primary Agent for writes
- Write operations like "create ADR stub" and "fill stage summary" must be queued

## 6. Log Quality

Logs should record increments and decisions, not generic weekly summaries.

Recommended template:

```text
<module/api/file> | change=<delta or current status> | evidence=<test/doc/path/ADR, use TBD if unknown> | next=<next concrete step> | risk=<none / specific risk>
```

Requirements:

- `<module/api/file>` should resolve to at least module/API/task-file/config-file level
- `change` should capture this specific increment/fix/migration/blocker
- `evidence` should prefer existing artifacts in current stage tasks/ACs/`.stage/`; use `TBD` when uncertain
- `next` must be immediately actionable
- Use `none` when there is no risk
- One log entry should describe one module topic; split cross-module updates

Anti-patterns:

- `optimized login`
- `handled some issues`
- `continue pushing`

## 7. ADR

Minimum four fields:

- Background / motivation
- Alternatives considered
- Decision
- Impact / consequences

Recommended skeleton:

```md
- ### [ADRS-XXX] | [YYYY-MM-DD] | [Title]
  - **Background / Motivation**: ...
  - **Alternatives**: option A vs option B
  - **Decision**: ...
  - **Impact / Consequences**: ...
```

If architecture is affected, include ADRS ID in the commit message.
