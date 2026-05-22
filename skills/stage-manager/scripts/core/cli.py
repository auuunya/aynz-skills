import argparse
import contextlib


def build_parser(version: str, allowed_log_status) -> argparse.ArgumentParser:
    """EN CLI EN，EN。"""
    parser = argparse.ArgumentParser(
        description="Stage-Manager: EN",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "EN:\n"
            "  stage.py init \"feature-auth\"\n"
            "  stage.py sync \"EN\" --task-name \"EN\"\n"
            "  stage.py sync \"[ADR] EN JWT\"\n"
            "  stage.py check TASK-001\n"
            "  stage.py switch stage-002-api.md\n"
            "  stage.py summary \"session snapshot\"\n"
            "  stage.py status --json\n"
            "  stage.py done\n"
        ),
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {version}")
    parser.add_argument("--root", help="Specify project root path")
    parser.add_argument("--json", action="store_true", help="EN JSON EN")
    sub = parser.add_subparsers(dest="cmd", title="EN", required=True)

    p = sub.add_parser("init", help="EN")
    p.add_argument("name", help="EN")

    p = sub.add_parser("sync", help="EN")
    p.add_argument("message", help="EN；[ADR] top EN")
    p.add_argument("--task-name", help="EN")
    p.add_argument("--status", default="in-progress", choices=sorted(allowed_log_status))
    p.add_argument("--next-action", help="EN")
    p.add_argument("--blocked-by", help="blockedEN ID")
    p.add_argument("--file", help="EN stage EN")

    p = sub.add_parser("summary", help="session snapshotEN")
    p.add_argument("text", nargs="?", help="snapshotEN")
    p.add_argument("--stage", action="store_true", help="EN(section 9)")
    p.add_argument("--name", help="EN")
    p.add_argument("--goal", help="EN")
    p.add_argument("--result", action="append", help="EN(EN)")
    p.add_argument("--audit", help="EN")
    p.add_argument("--debt", help="EN/EN")
    p.add_argument("--file", help="EN stage EN")

    p = sub.add_parser("intake", help="EN Backlog EN")
    p.add_argument("keyword", help="EN")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--file", help="EN stage EN")

    sub.add_parser("bootstrap", help="EN")

    p = sub.add_parser("status", help="EN")
    p.add_argument("--file", help="EN stage EN")

    p = sub.add_parser("validate", help="EN")
    p.add_argument("--file", help="EN stage EN")

    p = sub.add_parser("done", help="EN")
    p.add_argument("--force", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--file", help="EN stage EN")

    p = sub.add_parser("check", help="checked/uncheckedEN")
    p.add_argument("item_id", help="EN ID（EN TASK-001、AC-002）")
    p.add_argument("--uncheck", action="store_true", help="unchecked")
    p.add_argument("--file", help="EN stage EN")

    p = sub.add_parser("switch", help="ENtop Active stage")
    p.add_argument("target", help="ENStage fileEN")

    return parser


def determine_lock_target(args) -> str | None:
    """EN，EN。"""
    write_cmds = {"init", "sync", "summary", "intake", "done", "check", "switch"}
    if args.cmd not in write_cmds:
        return None
    if args.cmd == "summary":
        return "summary --stage" if args.stage else "summary"
    if args.cmd == "done":
        suffix = []
        if args.dry_run:
            suffix.append("--dry-run")
        if args.force:
            suffix.append("--force")
        return " ".join(["done"] + suffix).strip()
    return args.cmd


def execute_command(args, ctx) -> bool:
    """EN；EN。"""
    ok = True
    lock_target = determine_lock_target(args)
    lock_ctx = ctx.write_lock(lock_target) if lock_target else contextlib.nullcontext()

    try:
        with lock_ctx:
            if args.cmd == "init":
                ok = ctx.init_stage(args.name)

            elif args.cmd == "sync":
                ok = ctx.sync_log(args.message, args.task_name, args.status, args.next_action, args.blocked_by, args.file)

            elif args.cmd == "summary":
                if args.stage:
                    if not all([args.name, args.goal, args.audit, args.debt]):
                        ctx.info("[!] --stage EN --name --goal --audit --debt")
                        return False
                    ok = ctx.append_stage_summary(args.name, args.goal, args.result or [], args.audit, args.debt, args.file)
                else:
                    if not args.text:
                        ctx.info("[!] EN --stage EN text")
                        return False
                    ctx.update_session_summary(args.text)

            elif args.cmd == "intake":
                ok = ctx.intake_backlog(args.keyword, dry_run=args.dry_run, file_target=args.file)

            elif args.cmd == "bootstrap":
                ctx.render_dashboard("full")

            elif args.cmd == "status":
                ctx.render_dashboard("brief", file_target=getattr(args, "file", None))

            elif args.cmd == "validate":
                filename, filepath = ctx.resolve_stage_file(getattr(args, "file", None))
                if not filename or not filepath:
                    ctx.info("[!] ENtop ENStage file。")
                    return False
                errors, warns = ctx.validate_stage_document(filepath)
                ctx.emit("validate", {"file": filename, "errors": errors, "warnings": warns})
                if not errors and not warns:
                    ctx.info(f"[OK] EN: {filename}")
                else:
                    ctx.info(f"[CHECK] {filename}")
                    for err in errors:
                        ctx.info(f"  [ERROR] {err}")
                    for warn in warns:
                        ctx.info(f"  [WARN]  {warn}")
                    if errors:
                        ok = False

            elif args.cmd == "done":
                ok = ctx.archive_stage(force=args.force, dry_run=args.dry_run, file_target=getattr(args, "file", None))

            elif args.cmd == "check":
                ok = ctx.check_item(args.item_id, uncheck=args.uncheck, file_target=getattr(args, "file", None))

            elif args.cmd == "switch":
                ok = ctx.switch_stage(args.target)
    except RuntimeError as exc:
        ctx.info(str(exc))
        ok = False

    return ok
