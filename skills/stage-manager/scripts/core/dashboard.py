import re


def collect_dashboard_data(ctx, mode: str, file_target=None):
    """Collect dashboard data without direct output or index refresh."""
    filename, filepath = ctx.resolve_stage_file(file_target)
    data = {
        "stats": ctx.get_project_stats_dict(),
        "stats_str": ctx.get_project_stats(),
        "mode": mode,
    }
    if filename and filepath:
        data["current_stage"] = filename
        data["progress"] = ctx.calculate_progress(filepath)
        data["pending_tasks"] = ctx.get_pending_tasks(filepath)
    data["recent_sessions"] = re.findall(r"- \*\*session snapshot\*\*: (.*?)\n", ctx.read_text(ctx.cfg.session_file))[:3]
    data["recent_adrs"] = re.findall(r"^\d+\. (\[ADRS-\d+\].*?)$", ctx.read_text(ctx.cfg.adr_index), re.M)[-3:]
    if mode == "full":
        data["backlog_count"] = len(re.findall(r"^\s*-\s*\[ \]", ctx.read_text(ctx.cfg.backlog_file), re.M))
        data["skill_path"] = ctx.skill_path
        data["asset_root"] = ctx.cfg.asset_root
    return data


def render_dashboard_json(ctx, data):
    """Format dashboard data into JSON payload."""
    out = {"stats": data["stats"]}
    for key in ("current_stage", "progress", "recent_sessions", "recent_adrs",
                "backlog_count", "skill_path", "asset_root"):
        if key in data:
            out[key] = data[key]
    if "pending_tasks" in data:
        out["pending_tasks"] = data["pending_tasks"][:5]
    ctx.emit("dashboard", out)


def render_dashboard_text(ctx, data):
    """Format dashboard data for console output."""
    mode = data["mode"]
    stats_str = data["stats_str"]

    ctx.info("\n" + "=" * 50)
    ctx.info(" [BOOTSTRAP] Restoring session context..." if mode == "full" else f" [Project health] {stats_str}")
    ctx.info("=" * 50)

    if mode == "full":
        ctx.info(f"\n [Project overview] {stats_str}")

    if "current_stage" in data:
        progress = data["progress"]
        bar = "#" * int(progress / 5) + "-" * (20 - int(progress / 5))
        ctx.info(f" [{'Active stage' if mode == 'full' else 'Stage file'}] {data['current_stage']}")
        ctx.info(f" [Progress] [{bar}] {progress}%")
        pending = data.get("pending_tasks", [])
        if pending:
            limit = 3 if mode == "full" else 5
            plabel = "Next tasks" if mode == "full" else "Pending tasks"
            ctx.info(f"\n [{plabel}] (top {limit} items):")
            for task in pending[:limit]:
                ctx.info(f"  [ ] {task.strip()}")
    elif mode == "full":
        ctx.info(" [Active stage] No active stage")

    sessions = data.get("recent_sessions", [])
    if sessions:
        ctx.info(f"\n [{'Memory anchors' if mode == 'full' else 'Recent sessions'}] {'Recent sessionssnapshot' if mode == 'full' else '(latest 3)'}:")
        trunc = 100 if mode == "full" else 80
        for session in sessions[:3]:
            ctx.info(f"  > {session[:trunc]}{'...' if len(session) > trunc else ''}")
    elif mode == "full":
        ctx.info("\n [Memory anchors] NoneENsnapshot。")

    adrs = data.get("recent_adrs", [])
    if adrs:
        ctx.info("\n [Recent decisions] (latest 3):" if mode == "brief" else "\n [Recent decisions]:")
        for adr in adrs[-3:]:
            ctx.info(f"  * {adr.strip()}")

    if mode == "full":
        backlog_count = data.get("backlog_count", 0)
        if backlog_count > 0:
            ctx.info(f"\n [Backlog] {backlog_count} unclaimed tasks")
        ctx.info(f"\n [Skill Path] {ctx.skill_path}")
        ctx.info(f" [Asset root] {ctx.cfg.asset_root}")

    ctx.info("\n" + "=" * 50)
    if mode == "full":
        ctx.info(" [OK] Bootstrap completed.")
    ctx.info("=" * 50 + "\n")


def render_dashboard(ctx, mode: str = "full", file_target=None) -> bool:
    """Render dashboard and refresh heartbeat at the end."""
    data = collect_dashboard_data(ctx, mode, file_target)
    if ctx.json_mode:
        render_dashboard_json(ctx, data)
    else:
        render_dashboard_text(ctx, data)
    ctx.update_heartbeat()
    return True
