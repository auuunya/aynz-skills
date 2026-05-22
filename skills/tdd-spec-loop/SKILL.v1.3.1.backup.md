---
name: tdd-spec-loop
description: Convert a requirement into an AI-operable TDD loop with minimal, testable artifacts and objective checks. Use when users want reliable implementation through spec→test feedback.
version: 1.3.1
---

# tdd-spec-loop

Use when the user wants reliability via verifiable test artifacts, not blind coding.

## Commands (only 3)

- `/tdd` — default balanced mode
- `/tdd-fast` — minimal questions, fastest runnable loop
- `/tdd-deep` — clarification-first, stronger edge coverage

## Default behavior for a single requirement

If the user gives only one feature point, run **Admission Gate** before Auto-Scenario Bootstrap.

### Admission Gate (must pass)

1. **Single-endpoint rule**: maps to <= 1 endpoint (method + path).
2. **Single-transition rule**: observables come from one request/response transition.

If any rule fails:
- output `split_suggestion` (sub-requirements list),
- ask for confirmation once,
- if no reply, continue with the narrowest sub-requirement and mark others as `scope_overflow:TBD`.

### Auto-Scenario Bootstrap

1. Extract one happy-path assertion (`plain_assertion`).
2. Propose at least 2 failure branches.
3. Define objective observables (response/log/state/side-effect).
4. List assumptions + out_of_scope briefly and ask quick confirmation.
5. Generate minimal artifacts immediately after confirmation.

If the user does not answer clarification, continue with explicit assumptions and mark them as TBD.

## Modes

### Fast-Loop (`/tdd-fast`)

```text
Requirement -> 1 Scenario Card -> 1 Domain CLI -> 1 Test Instance -> 1 Mapping -> Check
```

Goal: get a runnable loop quickly.

### Balanced (`/tdd` default)

Same chain as Fast-Loop, but includes assumption check + at least one failure branch.

### Deep-Loop (`/tdd-deep`)

Must include:
- explicit failure branches (>=2)
- stronger observables and side-effect checks
- diagnosis template: `expected vs actual vs failed step`
- handoff-ready artifact notes

## Escalation rules (switch to Deep-Loop if any)

1. Same chain fails for 2+ rounds.
2. Scope touches security/permission/money.
3. Ambiguity affects assertion correctness.
4. Work requires cross-person/session handoff.

## Output contract (every round)

1. Generated/updated artifacts (exact names).
2. Current chain status.
3. Next concrete action.
4. Risks/TBDs.
5. Evaluation mode: `full_test` or `dry_run`.
6. `assumptions`, `out_of_scope`, `coverage_count` must be explicit.

## Artifact convention

- `.tdd-spec-env/domains/<domain>/`
- Required set: `scenario_card.md`, `domain_cli.md`, `instances.yaml`, `mapping.md`, `check_report.md`

## Minimal glossary

- `plain_assertion`: one-sentence truth-evaluable behavior assertion.
- `observable`: objectively retrievable evidence.
- `instance`: one executable test sample.
- `mapping`: relation from instance to test implementation.

## Hard bans

1. Write business code before mapping is stable.
2. Replace observables with subjective wording.
3. Claim pass from status code only (ignore side effects).
4. Report failure without `expected vs actual + failed step`.

## Probe boundary

- one domain first (default: `auth`)
- three instances minimum (`1 success + 2 failures`)
- stop at mapping + check report
- no feature expansion during probe
