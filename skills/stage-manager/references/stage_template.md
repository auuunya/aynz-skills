---
stage_id: "STAGE-XXX"
name: "TBD"
status: "PLANNING"
start_date: null
end_date: null
depends_on: []
milestone: null
---

# STAGE-XXX: TBD

---

<!--
Conventions:
- `.stages/` is maintained by scripts
- `.stage/` stores evidence artifacts
- Only one Agent may run stage write commands at a time
-->

<!-- @section:goals -->

## 1. Stage Goals

- [ ] [TARGET-001]: TBD
- [ ] [TARGET-002]: TBD

<!-- @section:scope -->

## 2. Scope

- [SCOPE-001] TBD

<!-- @section:out_of_scope -->

## 3. Out of Scope

- [OUT-SCOPE-001] TBD

<!-- @section:tasks -->

## 4. Task Breakdown

<!-- `executor`: agent / human / sub_agent -->
<!-- Keep code evidence in original paths; put non-code evidence under `.stage/` -->
<!-- `skills`, `deliverables`, `evidence`, and `due` below are schema placeholders only. Unless explicitly provided by user/context, do not write them as facts. -->

- [ ] [P0] [TASK-001] Task title | owner=unassigned | executor=agent | skills=[] | task_depends_on=[] | acceptance=[AC-001] | deliverables=[] | evidence=[] | due=YYYY-MM-DD
- [ ] [P0] [TASK-900] Stage acceptance | owner=unassigned | executor=agent | skills=[stage-reviewer] | task_depends_on=[] | acceptance=[AC-001,AC-002,AC-003,AC-004] | deliverables=[stage-review-report] | evidence=[.stage/reports/stage-review.md] | due=YYYY-MM-DD

<!-- @section:dod -->

## 5. Acceptance Criteria

<!-- `verify_by`: task_completion / evidence_review / metric_threshold / artifact_presence -->

- [ ] [AC-001] Functionality | verify_by=task_completion | required_tasks=[TASK-001] | required_checks=[critical_path_test] | evidence=[]
- [ ] [AC-002] Security | verify_by=evidence_review | required_tasks=[TASK-001] | required_checks=[permission_check,isolation_check] | evidence=[]
- [ ] [AC-003] Stability | verify_by=metric_threshold | required_tasks=[] | required_checks=[metrics_target_met] | evidence=[.stage/reports/perf.md]
- [ ] [AC-004] Change traceability | verify_by=artifact_presence | required_tasks=[TASK-001] | required_checks=[log_updated,adr_updated,summary_updated] | evidence=[.stage/logs/progress-log.md,.stage/docs/adr-001.md]

<!-- @section:risks -->

## 6. Risks & Mitigations

| Risk | Severity | Trigger signal | Mitigation | Rollback / Degrade plan |
| :--- | :------- | :------------- | :--------- | :---------------------- |

<!-- @section:log -->

## 7. Progress Log

<!--
- ### [LOG-XXX] | [YYYY-MM-DD] | [Topic] | [owner] | [Ver:git@commit-or-TBD]
  - **Status**: in-progress / done / blocked (Blocked by: XXX)
  - **Key progress**: one-sentence incremental update
  - **Module-level record**: <module/api/file> | change=<...> | evidence=<...> | next=<...> | risk=<...>
  - **Next action**: immediate next step
-->

- None

<!-- @section:adrs -->

## 8. Key Decisions (ADRs)

- None

<!-- @section:summary -->

## 9. Stage Summary

- None
