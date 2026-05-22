---
name: tdd-spec-loop
description: "Convert a requirement into an AI-operable TDD loop with minimal, testable artifacts and objective checks. Use when: 用户要求'测试驱动'、'TDD'、'写测试先'、'spec first'、'可靠实现'、'先写断言'、'确保能跑'、'回归保护'、'验收标准'、'分阶段交付'、reliable implementation、spec→test feedback."
version: 1.5.0-rc4
---

# tdd-spec-loop

Use when the user wants reliability via verifiable test artifacts, not blind coding.

## Quick Start

```text
Input:  "实现用户注册，邮箱唯一校验"
  ↓
Step 1  Admission Gate → PASS (single transition, testable)
  ↓
Step 2  Scenario Bootstrap
        → scenario_card.md  (plain_assertion + failure branches + observables)
        → domain_cli.md     (setup/invoke/verify/cleanup)
  ↓
Step 3  Fast-Loop (6-step)
        → instances.yaml → mapping.md → check_report.md
  ↓
Step 4  Optional: Deep-Loop diagnosis (if check_report shows failures)
  ↓
Output: 5 artifacts in ./tdd_artifacts/<domain>/
```

---

## Mode selection

| Mode | Command | When |
|------|---------|------|
| Fast-Loop | `tdd-spec-loop --fast` | 单跃迁、无复杂副作用 |
| Balanced | `tdd-spec-loop --mode balanced` | 中等复杂、需 failure branches |
| Deep-Loop | `tdd-spec-loop --deep` | 多状态转移、需完整 observables |

---

## Admission Gate


## Domain-specific validation rules

When Admission Gate identifies sensitive domains, apply mandatory checks below:

| Domain | Mandatory checks | Evidence in artifacts |
|---|---|---|
| money/payment | amount/currency/signature/idempotency/replay-window/ledger consistency | `instances.yaml` + `check_report.md` must include fields & verification results |
| security/auth | token expiry/audience/issuer/nonce/replay protection/permission boundary | `scenario_card.md` failure branches + `check_report.md` observables |
| webhook/integration | signature verification/timestamp skew/retry semantics/duplicate delivery | `instances.yaml` with replay inputs + `mapping.md` expected mapping |

**Hard rule:** If a mandatory check is missing, block delivery and return `schema_incomplete` in `check_report.md`.

Must pass before any coding. Block on ANY fail:

1. **Plain assertion** — reject fuzzy terms ("works fine" / "handles errors"). Require: `When <X>, expect <Y>.`
2. **Branch count** — 2+ failure branches (explicit boundary, conflict, permission, business rule, external dependency). 0 branches = reject.
3. **One-transition rule** — goal must describe one observable state change. Multi-goal → split via [Multi-requirement](#multi-requirement-handling).
4. **No hidden goal** — reject secret acceptance criteria.

> Fail → reason, ask for rewrite, wait.

---

## Auto-Scenario Bootstrap

Run auto. May ask 0-3 clarifying questions. Follow-up question = undecided branch, not new acceptance.

`scenario_card.md` must contain:
- plain_assertion (human language, no code)
- failure_branches (table)
- observables (protocol, not mental-state)

---

## Failure branch enumeration (systematic)

When generating failure branches, use these 5 categories to ensure coverage:

1. **Boundary violations** — null, empty, out-of-range, format mismatch
2. **State conflicts** — duplicate creation, concurrent modification, precondition missing
3. **Permission/auth** — unauthorized, expired token, scope insufficient
4. **Business rules** — limit exceeded, invariant violated, workflow order wrong
5. **External dependencies** — timeout, unavailable, malformed response, contract break

For each branch, specify: trigger condition → expected outcome → observable evidence.

---

## Multi-requirement handling

When the user request contains multiple requirements:

### Split decision template

Evaluate along 3 axes before splitting:

| Axis | Question | Example |
|------|----------|---------|
| **功能轴** | 是否描述了独立可测试的状态变化？ | "注册" vs "发邮件" → 可拆 |
| **风险轴** | 各部分失败影响是否不同？ | "幂等" 高风险 vs "字段校验" 低风险 → 拆 |
| **依赖轴** | B 是否依赖 A 的产出？ | "支付状态变更" 依赖 "验签" → 有序 |

### Default priority rules

1. money/security related → highest (always do first)
2. consistency/idempotency → high
3. core feature flow → medium
4. feature expansion/渠道适配 → lower

### Execution flow

1. Assign each requirement a `req-ID` (req-1, req-2, ...)
2. Run Admission Gate per requirement
3. Build priority table using split decision template
4. Process one at a time, each gets own `./tdd_artifacts/<domain>/req-N/`
5. After each: show check_report, ask continue or adjust

---

## Fast-Loop (6-step)

For single-transition requirements with minimal complexity.

**Goal**: fastest runnable loop. Failure branches simplified to top-2 only. Observables limited to direct outputs.

**Completion condition**: `Done when check_report.md exists (full_test or dry_run or fallback_mode)`

| Step | Input | Action | Output |
|------|-------|--------|--------|
| 1 | scenario_card | Generate 2-3 test instances (1 success + 1-2 failure) | instances.yaml |
| 2 | instances.yaml | For each instance, generate test file skeleton | test files |
| 3 | scenario_card + domain_cli | Implement minimal business code to pass success case | source code |
| 4 | test files | Run tests, capture results | test output |
| 5 | test output | Create mapping (instance → test → result) | mapping.md |
| 6 | mapping + test output | Generate check_report with pass/fail + diagnosis | check_report.md |

> **Step 6 blocked?** → jump to [Runtime Fallback](#runtime-fallback) table, then regenerate check_report with fallback_mode.

---

## Deep-Loop diagnosis (Balanced & Deep)

On test failure, diagnosis template:

```markdown
## Diagnosis: <instance_id>

### Symptom
- Status: FAIL
- Failed step: <step_name>
- Error: <exact error message>

### Evidence
- expected: <expected_value>
- actual: <actual_value>
- log snippet: <paste relevant output>

### Root cause hypothesis
1. <most likely cause with reasoning>
2. <alternative cause>

### Fix applied
- File: <path>
- Change: <before> → <after>
- Rationale: <why this fixes it>

### Verification
- Re-run: <command>
- Result: PASS/FAIL
```

---

## Checkpoints

Explicit pause-and-confirm points:

| # | When | Action | Default |
|---|------|--------|---------|
| 1 | After Admission Gate | Confirm split or proceed | auto-continue 1 round |
| 2 | After Scenario Bootstrap step 4 | Confirm assumptions | ask user |
| 3 | After each mode completion | Show check_report, ask continue | ask user |
| 4 | After 3+ consecutive dry_run | Escalate warning | must acknowledge |
| 5 | **Before domain_cli real execution** | Confirm env/data cleanup strategy | ask user |
| 6 | **On money/security domain hit** | Force Deep-Loop + second confirmation | must acknowledge |
| 7 | **After 2 consecutive failures on same instance** | Require diagnosis before retry | must acknowledge |
| 8 | **Before delivery** | Schema-check all 5 artifacts completeness | auto-check |

---

## Escalation rules

Hard stops — must warn or switch strategy:

- more than 2 clarifications on same topic — summarize and ask choose path
- observer cannot be made objective — convert to `dry_run` + manual confirmation
- real test still blocked — record evidence, proceed with mock/dry_run, mark `TBD`
- >3 TBDs — stop, return partial progress + recommendations

---

## Runtime Fallback

When execution environment is unavailable or unstable:

| Situation | Fallback | Artifact impact |
|-----------|----------|----------------|
| Test framework unavailable | `dry_run` mode + manual assertion verification | check_report: `mode: dry_run` |
| domain_cli execution fails | Fall back to plain assertion manual verification | check_report: `mode: manual_verify` |
| Environment missing (DB/Redis/service) | Mark `env_blocked` + record dependency | check_report: `mode: env_blocked`, list missing deps |
| Network unavailable | `offline_mode` + mock observables | check_report: `mode: offline`, mock data tagged |
| Dependency conflict | Isolate via virtualenv/container + document versions | check_report: `env: <isolation_method>` |
| Permission insufficient | Record required permissions + suggest fix | check_report: `permission_gap: <details>` |
| **Flaky test (intermittent)** | Fixed random seed + max 3 retries + tag `flaky:true` | check_report: `flaky: true, retries: N` |
| **External service unreachable** | Record/replay mock + `contract_snapshot` | check_report: `mode: contract_mock` |
| **State pollution** | Pre/post cleanup step + isolated data naming | check_report: `cleanup: pre+post` |

Fallback mode artifacts follow same schema but add `mode:` field to check_report.

---

## Output contract

```
./tdd_artifacts/<domain>/
├── scenario_card.md
├── domain_cli.md
├── instances.yaml
├── mapping.md
└── check_report.md
```

---

## Artifact templates (minimal schema)

> **Legend**: `[R]` = required, `[O]` = optional, `<auto>` = derivable from requirement

### scenario_card.md

```markdown
# Scenario: <name> <auto>

## Requirement
- Domain: <domain> <auto>
- Priority: P0/P1/P2 [R]
- Risk level: low/medium/high/critical [R]
- Acceptance threshold: <measurable criteria> [R]

## Plain assertion
When <trigger condition>, expect <observable outcome>.

## Failure branches
| # | Category | Trigger | Expected outcome | Observable |
|---|----------|---------|-----------------|------------|
| 1 | boundary | <condition> | <outcome> | <evidence> |
| 2 | state_conflict | <condition> | <outcome> | <evidence> |

## Observables
- output: <what to measure> [R]
- side_effect: <state change to verify> [R]
- protocol: <how to measure> [R]
```

### domain_cli.md

```markdown
# Domain CLI: <name> <auto>

## Runtime [R]
- Language: <e.g., python3.12>
- Dependencies: <e.g., pytest>=7.0>
- Timeout: <e.g., 30s>
- Entry dir: <working directory>

## Setup [R]
<command or steps to prepare environment>

## Invoke [R]
<command to trigger the behavior under test>

## Verify [R]
<command or check to validate the outcome>

## Cleanup [O]
<command to restore environment state>
```


### instances.yaml

```yaml
meta:
  domain: <domain>            # [R]
  generated_at: <ISO8601>     # [R]

cases:
  - id: <case_id>             # [R]
    type: success|failure     # [R]
    priority: P0|P1|P2        # [R]
    input:                    # [R]
      payload: <json_or_fields>
      headers: <key_values>
    expect:                   # [R]
      status_code: <int>
      observable: <text>
    pre_state: <text>         # [R]
    post_state: <text>        # [R]
    idempotency_key: <string> # [C-R]*
    replay_count: <int>       # [C-R]*

# [C-R] conditionally required when domain contains payment/webhook
```

Rendering rules:
- Use 2-space indentation only; no tabs.
- `cases` must be a YAML list, never a markdown table.
- Conditional required fields (`[C-R]`) must be promoted to required when requirement mentions idempotent/webhook/replay.

### mapping.md


```markdown
# Mapping: <domain> <auto>

| Instance ID | Test File | Test Function | Status | Commit Hash | Owner | Last Verified |
|-------------|-----------|---------------|--------|-------------|-------|---------------|
| <id> | <path> | <func> | PASS/FAIL | <hash> | <agent/user> | <ISO timestamp> |

## Coverage summary
- Total: N
- Passed: X
- Failed: Y
- Fallback: Z
```

### check_report.md

```markdown
# Check Report: <domain> <auto>

## Summary
- Mode: full_test / dry_run / manual_verify / env_blocked / offline / contract_mock [R]
- Total instances: N
- Passed: X
- Failed: Y
- Flaky: Z [O]

## Details
| Instance | Result | Duration | Evidence |
|----------|--------|----------|----------|
| <id> | PASS/FAIL | <time> | <link or log> |

## Diagnosis [R if any FAIL]
<use Deep-Loop diagnosis template>

## Environment [R]
- Runtime: <version>
- Dependencies: <list>
- Log path: <absolute path to test logs> [R]
- Evidence links: <screenshots, traces, traces> [O]
- Reproduce command: <exact command to re-run> [R]
```

---

## Ecosystem integration

| Tool | When to use | Integration point |
|------|-------------|-------------------|
| `grill-me` | Before TDD loop: stress-test scenario_card | After Scenario Bootstrap |
| `darwin-skill` | After TDD loop: evaluate artifact quality | After check_report generated |
| `vision_sop` | UI requirements: screenshot verification | During check_report evidence collection |

---

## Glossary

- **Plain assertion** — statement written in human language, not code
- **Dry run** — scenario played in imagination, output recorded as if executed
- **TBD** — unresolved decision point; capped at 3
- **Observable** — measurable output or state change, not mental-state description
- **Flaky** — test that intermittently passes/fails without code change
- **Contract snapshot** — recorded request/response pair for external service mock

---

## Hard bans

1. Write business code before mapping is stable.
2. Replace observables with subjective wording.
3. Claim pass from status code only (ignore side effects).
4. Report failure without `expected vs actual + failed step`.
5. Skip schema-required fields in artifacts.

## Probe boundary

- one domain first (default: `auth`, choose based on requirement domain keyword)
- three instances minimum (`1 success + 2 failures`)
- stop at mapping + check report
- no feature expansion during probe

> **Domain selection**: derive from requirement keywords. "login/auth/token" → `auth`, "payment/pay/refund" → `payment`, "user/register/profile" → `user`. If ambiguous, ask user.


---

## Checkpoint #6 and #7 interaction

- If Checkpoint #6 has already switched flow into Deep-Loop, repeated instance failures are handled by Deep-Loop diagnosis template.
- In that state, Checkpoint #7 does not request a second parallel escalation.
- Record one consolidated diagnosis block in `check_report.md`.


## A/B Evidence Protocol (with-skill vs baseline)

> 目标：将“实测表现”从 dry_run 提升为可复核证据。

### Required A/B Runs
- 对每个 `prompt_id` 运行两组：`baseline`（不加载skill）与 `with_skill`（加载本skill）
- 至少2个典型任务：
  - `prompt_A_user_register_unique_email`
  - `prompt_B_payment_webhook_idempotency`

### Metrics (必填)
- `pass_rate`
- `retry_count`
- `time_to_green`
- `defects_found`
- `reproducibility`（是否可用同命令复现）

### Evidence Output Contract
输出 `ab_evidence_report.md`，每个prompt必须包含：
- task context
- baseline result
- with_skill result
- delta summary
- risk notes

---

## Load Profile（分层加载）

- `short`: 仅 Admission + Fast-Loop + Checkpoint gate
- `standard`: short + templates index + fallback matrix
- `full`: standard + appendix examples + glossary

默认：`standard`。当上下文窗口紧张时强制 `short`，并在check_report标注 `load_profile`。

---

## Degrade-mode Check Report Snippets

### env_blocked
```yaml
mode: env_blocked
blocker: <tool/permission/network>
next_action: <manual_step_or_fallback>
```

### offline
```yaml
mode: offline
artifact_source: <local_cache|snapshot>
risk: <staleness_scope>
```

### contract_mock
```yaml
mode: contract_mock
contract_snapshot: <path_or_hash>
replay_case: <case_id>
```
