import re


def rewrite_stages_index(ctx, current_stage=None):
    """EN STAGES.md EN，ENtop /EN/EN。"""
    ctx.ensure_structure()
    existing = ctx.read_text(ctx.cfg.stages_index)

    qs_match = re.search(r"(^---\n\n## Quick Status.*$)", existing, re.M | re.S)
    quick_status = qs_match.group(1) if qs_match else (
        f"---\n\n## Quick Status\n- [HEARTBEAT] Init\n- [LAST_SESSION] NoneEN\n"
        f"- Last sync: {ctx.now_datetime()} | User: {ctx.get_sys_user()} | Version: {ctx.get_git_info()}\n"
    )

    active_files = ctx.list_md_files(ctx.cfg.stages_exec_dir)
    archived_files = ctx.list_md_files(ctx.cfg.archive_exec_dir)

    if not current_stage:
        old = re.search(r"`\.stages/stages/(stage-\d+-.*?\.md)`（ENtop EN）", existing)
        if old and old.group(1) in active_files:
            current_stage = old.group(1)
    if not current_stage and active_files:
        current_stage = active_files[0]

    lines = [
        "# Stages Index\n\n> This file is auto-maintained by stage-manager. All assets are under `.stages/`.\n\n---\n\n## Stage Index\n"
    ]
    idx = 1
    if active_files:
        ordered = [current_stage] + [f for f in active_files if f != current_stage] if current_stage else active_files
        for filename in ordered:
            tag = "ENtop EN" if filename == current_stage else "EN"
            lines.append(f"{idx}. `.stages/stages/{filename}`（{tag}）\n")
            idx += 1
    for filename in archived_files:
        lines.append(f"{idx}. `.stages/archive/stages/{filename}`（EN）\n")
        idx += 1

    lines.append("\n" + quick_status.strip("\n") + "\n")
    ctx.write_text(ctx.cfg.stages_index, "".join(lines))


def update_heartbeat(ctx):
    """EN STAGES.md EN、Recent sessionsENLast syncEN。"""
    ctx.ensure_structure()
    stats = ctx.get_project_stats()
    session = ctx.get_last_session_text()
    now = ctx.now_datetime()
    user = ctx.get_sys_user()
    ver = ctx.get_git_info()

    lines = ctx.read_text(ctx.cfg.stages_index).splitlines(True)
    found_sync = False
    for index, line in enumerate(lines):
        if "[HEARTBEAT]" in line:
            lines[index] = f"- [HEARTBEAT] {stats}\n"
        elif "[LAST_SESSION]" in line:
            lines[index] = f"- [LAST_SESSION] {session}\n"
        elif "Last sync" in line:
            lines[index] = f"- Last sync: {now} | User: {user} | Version: {ver}\n"
            found_sync = True
    if not found_sync:
        lines.append(f"- Last sync: {now} | User: {user} | Version: {ver}\n")
    ctx.write_text(ctx.cfg.stages_index, "".join(lines))


def update_adr_index(ctx, clean_msg: str, stage_file: str, is_archive: bool = False) -> str:
    """EN ADRS.md ENDecision IndexEN，ENLast updatedEN。"""
    ctx.ensure_structure()
    lines = ctx.read_text(ctx.cfg.adr_index).splitlines(True)
    count = ctx.count_adrs_from_index()
    adr_id = f"ADRS-{count + 1:03d}"
    prefix = ".stages/archive/stages/" if is_archive else ".stages/stages/"
    entry = f"{count + 1}. [{adr_id}] {clean_msg} ({prefix}{stage_file})\n"

    insert_idx = next((i + 1 for i, line in enumerate(lines) if "Decision Index" in line), -1)
    if insert_idx != -1:
        lines.insert(insert_idx + count, entry)
    else:
        lines.append("\n" + entry)

    for index, line in enumerate(lines):
        if "Total decisions" in line:
            lines[index] = f"- Total decisions: {count + 1}\n"
        elif "Last updated" in line:
            lines[index] = f"- Last updated: {ctx.now_datetime()}\n"

    ctx.write_text(ctx.cfg.adr_index, "".join(lines))
    return adr_id


def update_session_summary(ctx, text: str):
    """EN STAGE_SESSIONS.md ENsession snapshot，EN。"""
    ctx.ensure_structure()
    clean = ctx.clean_summary_text(text)
    active_file, _ = ctx.get_latest_stage_info()
    now = ctx.now_datetime()

    lines = ctx.read_text(ctx.cfg.session_file).splitlines(True)
    entry = f"### [{now}] Stage: {active_file or 'Global'}\n- **session snapshot**: {clean}\n\n"

    insert_idx = next((i + 1 for i, line in enumerate(lines) if "Session Summaries" in line), -1)
    if insert_idx != -1:
        lines.insert(insert_idx + 1, entry)
    else:
        lines.append(entry)

    for index, line in enumerate(lines):
        if line.startswith("- Recent Records") or line.startswith("- NoneEN"):
            lines[index] = f"- Recent Records: [{now}] {clean[:60]}...\n"
            break

    indices = [i for i, line in enumerate(lines) if line.startswith("### [")]
    if len(indices) > ctx.session_max_entries:
        lines = lines[:indices[ctx.session_max_entries]]

    ctx.write_text(ctx.cfg.session_file, "".join(lines))
    ctx.update_heartbeat()
