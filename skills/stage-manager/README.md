# Stage-Manager

> An industrial-grade automated stage planning and management system designed for AI Agent workflows.

`stage-manager` is a lightweight, standardized project lifecycle management Skill. It follows the isolation principle of “one stage, one document,” and combines automation scripts, standardized templates, and reference conventions to ensure project progress, architecture decision records (ADRS), and session summaries (STAGE_SESSIONS) are captured in a structured way. All runtime assets are centrally managed under the `.stages/` directory to keep the project root clean, auditable, and recoverable.

## CLI Entry

- The current stable entry is `scripts/stage.py`.
- The semantic aliases like `stage:*` inside the skill are all mapped to:

```bash
python3 <skill-path>/scripts/stage.py <subcommand>
```

- Common examples:

```bash
python3 scripts/stage.py bootstrap
python3 scripts/stage.py init "feature-auth"
python3 scripts/stage.py sync "[ADR] Use Redis as the cache layer"
python3 scripts/stage.py status --file stage-002-payment-fix.md
```

## Core Features

- **Centralized Runtime Assets**  
  All management files (board, decisions, logs, backlog) are stored under `.stages/`.
- **Standardized Stage Documents**  
  Each stage document follows a unified schema including goals, scope, task breakdown, acceptance criteria, risks, logs, ADRs, and stage summary.
- **Architecture Decisions with IDs**  
  Automatically generates unique IDs for architecture decisions (e.g., `[ADRS-001]`) and supports precise cross-document references.
- **Session State Compression (Save/Load)**  
  Uses `summary` and `bootstrap` mechanisms to mitigate memory loss and context bloat in long conversations.
- **DoD Hard Gate**  
  Automatically checks `## 5. Acceptance Criteria` before archive, preventing pseudo-closure where tasks are done but acceptance is not.
- **Backlog Intake and Task Routing**  
  Supports claiming tasks from `BACKLOGS.md` by keyword; during archive, unfinished tasks and out-of-scope items are automatically routed to `[TECH_DEBT]` and `[ROADMAP]` respectively.
- **Multi-Stage Operations**  
  Supports explicitly operating on other stage files via `--file`, instead of only relying on the current stage.
- **Single-Writer Protection**  
  All commands that modify `.stages/` or stage documents are guarded by a script-level single-writer lock to avoid index conflicts from concurrent writes.

## Runtime Asset Directory

```text
.stages/                           # Auto-generated runtime asset directory (at project root)
├── STAGES.md                      # Stage board (stats, current stage, other stages, recent snapshots)
├── ADRS.md                        # Central architecture decision index (with standard IDs)
├── STAGE_SESSIONS.md              # Session compression log (sliding window)
├── BACKLOGS.md                    # Cross-stage task pool
├── stages/                        # All unarchived stage docs; only one is marked as "current stage"
└── archive/
    └── stages/                    # Archived stage docs
```

## Script Structure

```text
scripts/
├── stage.py                       # External CLI entry
└── core/                          # Internal implementation modules
    ├── cli.py                     # Argument parsing and command dispatch
    ├── runtime.py                 # Paths, IO, output, write lock
    ├── doc.py                     # frontmatter, sections, parsing, rendering, stats
    ├── commands.py                # init/check/switch/intake and related commands
    ├── ops.py                     # sync/summary/done write operations
    ├── indexes.py                 # STAGES/ADRS/session index maintenance
    ├── validate.py                # P0/DoD/evidence/schema validation
    └── dashboard.py               # bootstrap/status display
```

- `scripts/stage.py` is responsible for a stable entry contract, keeping skill, tests, and external calls consistent.
- `scripts/core/*.py` is internal implementation; if you are only using the skill, you do not need to operate on these modules directly.

## Stage Status Semantics

- In `STAGES.md`, `current stage` is the unique pointer representing the default read/write target.
- `other stages` are unarchived stages still under `.stages/stages/` but not currently selected.
- `archived stages` are stage files moved to `.stages/archive/stages/`.
- When operating on other stages, prefer `--file <stage-file>` instead of switching the current stage just for temporary edits.

## Write Constraints

- `init`, `sync`, `summary`, `intake`, `check`, `switch`, and `done` are write commands and should be executed serially.
- If two write commands run concurrently, the script returns `[BUSY]`; wait for the previous command to finish before retrying.
- `.stages/STAGES.md`, `.stages/ADRS.md`, `.stages/BACKLOGS.md`, and `.stages/STAGE_SESSIONS.md` should only be maintained via `scripts/stage.py`; manual index edits are not recommended.
