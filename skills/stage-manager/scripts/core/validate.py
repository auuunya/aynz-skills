import os
import re


def check_p0_completed(ctx, filepath):
    """EN P0 EN，EN itemsEN。"""
    def _is_unchecked_p0(line: str) -> bool:
        """Check whether task line is an unchecked P0 task."""
        parsed = ctx.parse_task_line(line)
        return parsed is not None and parsed["priority"] == "P0" and not parsed["checked"]

    return ctx.check_section_items(filepath, 4, _is_unchecked_p0)


def check_dod_completed(ctx, filepath):
    """ENchecked，EN itemsEN。"""
    return ctx.check_section_items(filepath, 5, lambda line: re.match(r"^\s*-\s*\[ \]", line) is not None)


def has_summary_content(ctx, filepath):
    """EN section EN。"""
    if not os.path.exists(filepath):
        return False
    sec = ctx.find_section_block(ctx.read_text(filepath), 9)
    return sec is not None and not re.fullmatch(r"\s*-\s*None\s*", sec[3].strip())


def check_implementation_evidence(ctx, filepath):
    """EN、EN evidence。"""
    if not os.path.exists(filepath):
        return False, []
    content = ctx.read_text(filepath)
    if ctx.infer_stage_type(content) != "implementation":
        return True, []

    evidence_paths = []
    for sec_no, parser in [(4, ctx.parse_task_line), (5, ctx.parse_ac_line)]:
        sec = ctx.find_section_block(content, sec_no)
        if not sec:
            continue
        for line in re.findall(r"^\s*-\s*\[[ xX]\].*$", sec[3], re.M):
            parsed = parser(line)
            if parsed:
                evidence_paths.extend(parsed["evidence"])

    real = [path for path in dict.fromkeys(evidence_paths) if path and not path.startswith(".stage/")]
    return len(real) > 0, real


def validate_stage_document(ctx, filepath):
    """EN schema、EN evidence EN。"""
    errors = []
    warns = []

    if not os.path.exists(filepath):
        return [f"EN: {filepath}"], []

    content = ctx.read_text(filepath)
    fm, _ = ctx.parse_frontmatter(content)

    for key in ctx.fm_key_order:
        if key not in fm:
            errors.append(f"frontmatter EN: {key}")
    if "status" in fm and fm["status"] not in ctx.allowed_stage_status:
        errors.append(f"stage status invalid: {fm['status']}")

    for date_key in ("start_date", "end_date"):
        if date_key in fm and fm[date_key] not in (None, "null"):
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(fm[date_key])):
                errors.append(f"{date_key} ENinvalid: {fm[date_key]}")

    if fm.get("status") in {"COMPLETED", "ARCHIVED"} and not fm.get("end_date"):
        errors.append("EN COMPLETED/ARCHIVED EN，end_date EN null")
    if fm.get("status") in {"PLANNING", "IN_PROGRESS", "TESTING"} and fm.get("end_date"):
        warns.append("EN end_date")

    for sec in range(1, 10):
        if not ctx.find_section_block(content, sec):
            errors.append(f"EN section: ## {sec}.")

    task_ids, ac_ids = [], []
    task_to_ac = {}
    ac_to_task = {}

    for sec_no, parser, validator, id_key, ref_key in [
        (4, ctx.parse_task_line, ctx.validate_task_line, "task_id", "acceptance"),
        (5, ctx.parse_ac_line, ctx.validate_ac_line, "ac_id", "required_tasks"),
    ]:
        sec = ctx.find_section_block(content, sec_no)
        if not sec:
            continue
        lines = re.findall(r"^\s*-\s*\[[ xX]\].*$", sec[3], re.M)
        if not lines:
            warns.append(f"{'EN' if sec_no == 4 else 'EN'} section ENNone checklist")
        for line in lines:
            errors.extend(validator(line))
            parsed = parser(line)
            if not parsed:
                continue
            item_id = str(parsed[id_key])
            if sec_no == 4:
                task_ids.append(item_id)
                task_to_ac[item_id] = list(parsed[ref_key])
                if parsed["priority"] == "P0" and not parsed["evidence"]:
                    warns.append(f"{item_id} EN P0 EN evidence EN")
            else:
                ac_ids.append(item_id)
                ac_to_task[item_id] = list(parsed[ref_key])
                if parsed["verify_by"] == "artifact_presence" and not parsed["evidence"]:
                    errors.append(f"{item_id} verify_by=artifact_presence EN evidence EN")
                elif not parsed["evidence"]:
                    warns.append(f"{item_id} evidence EN")

    if len(task_ids) != len(set(task_ids)):
        errors.append("EN ID EN")
    if len(ac_ids) != len(set(ac_ids)):
        errors.append("EN ID EN")

    ac_set, task_set = set(ac_ids), set(task_ids)
    for task_id, refs in task_to_ac.items():
        for ac in refs:
            if ac not in ac_set:
                errors.append(f"{task_id} EN: {ac}")
    for ac_id, refs in ac_to_task.items():
        for task_id in refs:
            if task_id not in task_set:
                errors.append(f"{ac_id} EN: {task_id}")

    if "TASK-900" not in task_set:
        warns.append("EN TASK-900 EN")

    for sec_no, label in [(7, "EN"), (9, "EN")]:
        sec = ctx.find_section_block(content, sec_no)
        if sec and re.fullmatch(r"\s*-\s*None\s*", sec[3].strip()):
            warns.append(f"{label}EN")

    if ctx.infer_stage_type(content) == "implementation":
        ok, _ = ctx.check_implementation_evidence(filepath)
        if not ok:
            warns.append("EN/EN/EN evidence")

    return errors, warns
