import os
import re
import shutil


def sync_log(ctx, message: str, task_name=None, status: str = "in-progress",
             next_action=None, blocked_by=None, file_target=None) -> bool:
    """Append logs to stage document; when prefixed with `[ADR]`, also write ADR stub and index."""
    filename, filepath = ctx.resolve_stage_file(file_target)
    if not filename or not filepath:
        ctx.info("[!] ENtop ENStage file。")
        return False
    if status not in ctx.allowed_log_status:
        ctx.info(f"[!] Invalid log status: {status}，allowed values: {', '.join(sorted(ctx.allowed_log_status))}")
        return False

    content = ctx.read_text(filepath)

    if message.startswith("[ADR]"):
        clean_msg = message[5:].strip() or "TBD"
        adr_id = ctx.update_adr_index(clean_msg, filename, is_archive=("archive" in filepath))
        content = ctx.prepend_to_section_body(
            content,
            8,
            ctx.render_adr_entry(adr_id, clean_msg),
            remove_placeholder_tbd=True,
        )
        ctx.info(f"[OK] Created ADR stub: {adr_id}")

    content = ctx.prepend_to_section_body(
        content,
        7,
        ctx.render_log_entry(filepath, message, task_name, status, next_action, blocked_by),
        remove_placeholder_tbd=True,
    )

    fm, _ = ctx.parse_frontmatter(content)
    cur_status = str(fm.get("status"))
    new_status = "IN_PROGRESS" if cur_status == "PLANNING" else cur_status
    if new_status != fm.get("status"):
        content = ctx.replace_frontmatter(content, {"status": new_status})

    ctx.write_text(filepath, content)
    ctx.update_heartbeat()
    ctx.info(f"[OK] Synced to {filename}")
    return True


def append_stage_summary(ctx, name: str, milestone_goal: str, core_results,
                         change_audit: str, tech_debt: str, file_target=None) -> bool:
    """Append summary record to stage doc section 9 and refresh heartbeat."""
    filename, filepath = ctx.resolve_stage_file(file_target)
    if not filename or not filepath:
        ctx.info("[!] ENtop ENStage file。")
        return False
    content = ctx.read_text(filepath)
    entry = ctx.render_summary_entry(filepath, name, milestone_goal, core_results, change_audit, tech_debt)
    content = ctx.prepend_to_section_body(content, 9, entry, remove_placeholder_tbd=True)
    ctx.write_text(filepath, content)
    ctx.update_heartbeat()
    ctx.info(f"[OK] Stage summary written: {filename}")
    return True


def archive_stage(ctx, force: bool = False, dry_run: bool = False, file_target=None) -> bool:
    """Complete archive flow: validate gates, route backlog, move files, update Session Summaries."""
    filename, src = ctx.resolve_stage_file(file_target)
    if not filename or not src:
        ctx.info("[!] ENtop ENStage file。")
        return False
    if src.startswith(os.path.abspath(ctx.cfg.archive_exec_dir)):
        ctx.info("[!] EN archive EN。")
        return False

    errors, warns = ctx.validate_stage_document(src)
    if errors and not force:
        ctx.info("[!] ENtop EN：")
        for err in errors:
            ctx.info(f"  [ERROR] {err}")
        for warn in warns:
            ctx.info(f"  [WARN]  {warn}")
        ctx.info("[?] Please fix the ERRORs above. Use done --force only if explicitly needed.")
        return False

    gates = [
        (ctx.check_p0_completed, "There are unfinished [P0] tasks", "Please complete the P0 tasks first"),
        (ctx.check_dod_completed, "## 5. Acceptance criteria (DoD) not fully passed", "Please complete the acceptance items first"),
    ]
    for checker, fail_msg, fix_msg in gates:
        ok, pending = checker(src)
        if not ok and not force:
            ctx.info(f"\n[!] Archive rejected: {fail_msg}。")
            for item in pending:
                ctx.info(f"  {item}")
            ctx.info(f"\n[?] {fix_msg}。EN: done --force")
            return False

    if not ctx.has_summary_content(src) and not force:
        ctx.info("\n[!] Archive rejected: ## 9. EN EN。")
        ctx.info("[?] Please add stage summary first. Use done --force only if needed.")
        return False

    impl_ok, _ = ctx.check_implementation_evidence(src)
    if not impl_ok and not force:
        ctx.info("\n[!] Archive rejected: Implementation stage has no verifiable code/test/config evidence yet.")
        ctx.info("[?] Please add verifiable evidence first. Use done --force only if needed.")
        return False

    if dry_run:
        ctx.info(f"[DRY-RUN] Will archive stage: {filename}")
        for warn in warns:
            ctx.info(f"[DRY-RUN][WARN] {warn}")
        return True

    content = ctx.read_text(src)

    oos = ctx.find_section_block(content, 3)
    if oos:
        items = re.findall(r"^\s*-\s+\[OUT-SCOPE-\d+\].*$", oos[3], re.M)
        if items:
            ctx.route_backlog(items, filename, "[ROADMAP]")

    tasks = ctx.find_section_block(content, 4)
    if tasks:
        unfinished = re.findall(r"^\s*-\s*\[ \].*$", tasks[3], re.M)
        if unfinished:
            ctx.route_backlog(unfinished, filename, "[TECH_DEBT]")

    summary = ctx.extract_summary_brief(content)
    content = ctx.replace_frontmatter(content, {"status": "COMPLETED", "end_date": ctx.now_date()})

    if not ctx.has_summary_content(src):
        content = ctx.replace_section_body(content, 9, ctx.render_summary_entry(
            src,
            "Archive Summary",
            "Stage archived.",
            ["Stage done/archive flow."],
            "Status and end date auto-filled during archive.",
            "Routed to Backlog by policy.",
        ))

    ctx.write_text(src, content)

    dst = os.path.join(ctx.cfg.archive_exec_dir, filename)
    shutil.copy2(src, dst)
    if not os.path.exists(dst) or os.path.getsize(dst) != os.path.getsize(src):
        ctx.info("[!] Archive copy verification failed; source file retained.")
        return False
    os.remove(src)

    remaining = ctx.list_md_files(ctx.cfg.stages_exec_dir)
    ctx.rewrite_stages_index(current_stage=remaining[0] if remaining else None)
    ctx.update_session_summary(f"[archive automation] EN {filename} closed: {summary}")
    ctx.info("[OK] Archive completed.")
    return True
