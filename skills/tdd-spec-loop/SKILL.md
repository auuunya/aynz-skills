---
name: tdd-spec-loop
description: Convert requirement → executable TDD probe artifacts with objective checks and explicit eval mode.
version: 1.5.1
---

# tdd-spec-loop (compact)

## Trigger
Use when user asks TDD/spec-first/reliable implementation/regression-ready delivery.

## Commands
- `/tdd` (balanced, default)
- `/tdd-fast` (minimal questions, fastest runnable loop)
- `/tdd-deep` (clarification + stronger failure/diagnosis)

## Admission Gate (must pass before artifact generation)
1) Single-endpoint rule: scope maps to <=1 endpoint (method+path)
2) Single-transition rule: observables come from one request/response transition
If fail: output `split_suggestion`, ask once, then continue with narrowest sub-scope and mark others `scope_overflow:TBD`.

## Standard Loop
Requirement → Scenario Card → Domain CLI → Instances → Mapping → Check Report

## Required outputs (every round)
1) generated/updated artifacts (exact names)
2) chain status
3) next concrete action
4) risks/TBD
5) eval_mode (`full_test` | `dry_run`)
6) explicit `assumptions`, `out_of_scope`, `coverage_count`

## Artifact contract
Root: `./tdd_artifacts/<domain>/`
Required files:
- `scenario_card.md`
- `domain_cli.md`
- `instances.yaml`
- `mapping.md`
- `check_report.md`

## Minimum probe boundary
- one domain first (`auth` default)
- >=3 instances (`1 success + 2 failures`)
- stop at mapping + check_report
- no feature expansion during probe

## Mode policy
### Fast
Single happy-path + essential observables; minimize clarification.

### Balanced (default)
Happy-path + >=1 failure branch + assumption check.

### Deep
Must include:
- >=2 failure branches
- side-effect observables (not status-only)
- diagnosis template: `expected vs actual vs failed_step`
- handoff-ready notes

## Escalation to Deep (any hit)
- same chain fails >=2 rounds
- security/permission/money involved
- ambiguity affects assertion correctness
- cross-person/session handoff required

## A/B Evidence Protocol (for quality claims)
When claiming “improved skill quality”, run >=2 prompts with baseline vs with-skill.
For each pair record in `check_report.md`:
- pass_rate
- retry_count
- time_to_green
- failure_taxonomy
Conclusion must separate: quality delta vs latency delta.

## Degrade modes (must be explicit)
- `env_blocked`: blocker + next_action
- `offline`: local artifact source + staleness risk
- `contract_mock`: contract snapshot + replay case

## Hard bans
1) No business-code-first before mapping stabilizes
2) No subjective observables
3) No PASS claim from status code only
4) No failure report without `expected vs actual + failed_step`

## Minimal glossary
- plain_assertion: one-sentence truth-evaluable behavior
- observable: objectively retrievable evidence
- instance: executable test sample
- mapping: test-instance ↔ implementation relation
