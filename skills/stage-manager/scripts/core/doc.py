#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Stage-Manager document utilities: frontmatter, sections, parsing, rendering, stats."""

import os
import re
from typing import Any, Callable, Dict, List, Optional, Tuple

from .runtime import (
    ALLOWED_EXECUTOR,
    ALLOWED_VERIFY_BY,
    cfg,
    ensure_structure,
    get_git_info,
    get_sys_user,
    now_date,
    read_text,
)


FM_KEY_ORDER = ["stage_id", "name", "status", "start_date", "end_date", "depends_on", "milestone"]

SECTION_ANCHORS = {
    1: "goals",
    2: "scope",
    3: "out_of_scope",
    4: "tasks",
    5: "dod",
    6: "risks",
    7: "log",
    8: "adrs",
    9: "summary",
}


def parse_frontmatter(content: str) -> Tuple[dict, str]:
    """EN frontmatter EN。"""
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", content, re.S)
    if not match:
        return {}, content
    data: Dict[str, object] = {}
    for line in match.group(1).splitlines():
        line = re.sub(r"\s+#.*$", "", line.strip())
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        value = value.strip()
        if value == "null":
            data[key.strip()] = None
        elif value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            data[key.strip()] = [item.strip().strip('"') for item in inner.split(",") if item.strip()] if inner else []
        elif value.startswith('"') and value.endswith('"'):
            data[key.strip()] = value[1:-1]
        else:
            data[key.strip()] = value
    return data, match.group(2)


def dump_frontmatter(data: dict) -> str:
    """EN frontmatter。"""
    lines = ["---"]
    for key in FM_KEY_ORDER:
        value = data.get(key)
        if value is None:
            lines.append(f"{key}: null")
        elif isinstance(value, list):
            joined = ", ".join(f'"{item}"' if " " in str(item) else str(item) for item in value) if value else ""
            lines.append(f"{key}: [{joined}]")
        else:
            lines.append(f'{key}: "{value}"')
    lines.append("---")
    return "\n".join(lines)


def replace_frontmatter(content: str, updates: dict) -> str:
    """EN frontmatter EN。"""
    current, body = parse_frontmatter(content)
    current.update(updates)
    return dump_frontmatter(current) + "\n" + body.lstrip("\n")


def update_title(content: str, stage_id: str, name: str) -> str:
    """EN Markdown EN，EN stage_id EN。"""
    new_title = f"# {stage_id}: {name}"
    if re.search(r"^# ", content, re.M):
        return re.sub(r"^# .*?$", new_title, content, count=1, flags=re.M)
    return new_title + "\n\n" + content


def find_section_block(content: str, section_no: int) -> Optional[Tuple[int, int, str, str]]:
    """EN `@section` EN，EN `## N.` EN。"""
    anchor_name = SECTION_ANCHORS.get(section_no)
    if anchor_name:
        anchor_pat = rf"<!--\s*@section:{re.escape(anchor_name)}\s*-->\s*\n"
        anchor_match = re.search(anchor_pat, content)
        if anchor_match:
            after = content[anchor_match.end():]
            header_match = re.match(r"(\s*^## \d+\..*?$)(.*?)(?=^## \d+\.|\Z)", after, re.M | re.S)
            if header_match:
                abs_start = anchor_match.start()
                abs_end = anchor_match.end() + header_match.end()
                return abs_start, abs_end, header_match.group(1).strip(), header_match.group(2)

    match = re.search(rf"(^## {section_no}\..*?$)(.*?)(?=^## \d+\.|\Z)", content, re.M | re.S)
    return (match.start(), match.end(), match.group(1), match.group(2)) if match else None


def _get_anchor_prefix(content_slice: str, section_no: int) -> str:
    """EN section EN，EN。"""
    anchor_name = SECTION_ANCHORS.get(section_no)
    if anchor_name:
        match = re.search(rf"(<!--\s*@section:{re.escape(anchor_name)}\s*-->\s*\n)", content_slice)
        if match:
            return match.group(1)
    return ""


def replace_section_body(content: str, section_no: int, new_body: str) -> str:
    """EN section EN，EN。"""
    block = find_section_block(content, section_no)
    if not block:
        return content
    start, end, header, _ = block
    prefix = _get_anchor_prefix(content[start:end], section_no)
    return content[:start] + prefix + header + "\n\n" + new_body.strip("\n") + "\n" + content[end:]


def prepend_to_section_body(content: str, section_no: int, block_text: str, remove_placeholder_tbd: bool = False) -> str:
    """EN section EN，EN `- None` EN。"""
    section = find_section_block(content, section_no)
    if not section:
        return content
    start, end, header, body = section
    body_text = body.strip("\n")
    if remove_placeholder_tbd:
        body_text = re.sub(r"^\s*-\s*None\s*$", "", body_text, flags=re.M).strip("\n")
    parts = [part for part in [block_text.strip("\n"), body_text.strip("\n")] if part.strip()]
    new_body = "\n\n".join(parts) if parts else "- None"
    prefix = _get_anchor_prefix(content[start:end], section_no)
    return content[:start] + prefix + header + "\n\n" + new_body + "\n" + content[end:]


def _extract_stage_num(filename: str) -> int:
    """ENStage fileEN，EN。"""
    match = re.search(r"stage-(\d+)-", filename)
    return int(match.group(1)) if match else 999999


def list_md_files(directory: str) -> List[str]:
    """EN Markdown EN。"""
    if not os.path.exists(directory):
        return []
    return sorted([filename for filename in os.listdir(directory) if filename.endswith(".md")], key=_extract_stage_num)


def get_latest_stage_info() -> Tuple[Optional[str], str]:
    """ENtop Stage fileEN，ENActive stageEN。"""
    ensure_structure()
    active_files = list_md_files(cfg.stages_exec_dir)
    max_num = f"{max((_extract_stage_num(filename) for filename in active_files), default=0):03d}"
    content = read_text(cfg.stages_index)
    if not content:
        return None, max_num
    match = re.search(r"`\.stages/stages/(stage-\d+-.*?\.md)`（ENtop EN）", content)
    return (match.group(1) if match else None), max_num


def resolve_stage_file(target: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
    """ENStage fileEN，ENtop EN、EN/ENPathEN。"""
    if not target:
        active_file, _ = get_latest_stage_info()
        if not active_file:
            return None, None
        return active_file, os.path.join(cfg.stages_exec_dir, active_file)
    if os.path.isabs(target) and os.path.exists(target):
        return os.path.basename(target), target
    if os.path.exists(target):
        return os.path.basename(target), os.path.abspath(target)
    for base in [cfg.stages_exec_dir, cfg.archive_exec_dir]:
        candidate = os.path.join(base, target)
        if os.path.exists(candidate):
            return os.path.basename(candidate), candidate
    return None, None


def _next_id(filepath: str, prefix: str, *, max_below: Optional[int] = None) -> str:
    """EN ID，EN。"""
    nums = []
    for match in re.finditer(rf"\[{prefix}(\d{{3}})\]", read_text(filepath)):
        value = int(match.group(1))
        if max_below is None or value < max_below:
            nums.append(value)
    return f"{prefix}{max(nums, default=0) + 1:03d}"


def count_adrs_from_index() -> int:
    """EN ADR EN itemsEN。"""
    return len(re.findall(r"\[ADRS-\d+\]", read_text(cfg.adr_index)))


def get_last_session_text() -> str:
    """EN itemssession snapshotEN。"""
    match = re.search(r"- \*\*session snapshot\*\*: (.*?)\n", read_text(cfg.session_file))
    return match.group(1).strip() if match else "NoneEN"


def parse_bracket_list(text: str) -> List[str]:
    """EN `[a,b,c]` EN。"""
    text = text.strip()
    if not text.startswith("[") or not text.endswith("]"):
        return []
    inner = text[1:-1].strip()
    return [item.strip().strip('"') for item in inner.split(",") if item.strip()] if inner else []


def _parse_kv_tail(tail: str) -> Tuple[str, Dict[str, str]]:
    """EN `name | k1=v1 | k2=v2` EN。"""
    parts = [part.strip() for part in tail.split("|")]
    name = parts[0].strip().replace("**", "") if parts else ""
    fields: Dict[str, str] = {}
    for part in parts[1:]:
        if "=" in part:
            key, value = part.split("=", 1)
            fields[key.strip()] = value.strip()
    return name, fields


def parse_task_line(task_line: str) -> Optional[Dict[str, object]]:
    """EN。"""
    match = re.match(r"^\-\s*\[([ xX])\]\s+\[(P\d+)\]\s+\[(TASK-\d{3}|TASK-TBD)\]\s+(.*)$", task_line.strip())
    if not match:
        return None
    name, fields = _parse_kv_tail(match.group(4))
    return {
        "checked": match.group(1).lower() == "x",
        "priority": match.group(2),
        "task_id": match.group(3),
        "name": name,
        "owner": fields.get("owner", ""),
        "executor": fields.get("executor", ""),
        "skills": parse_bracket_list(fields.get("skills", "[]")),
        "task_depends_on": parse_bracket_list(fields.get("task_depends_on", "[]")),
        "acceptance": parse_bracket_list(fields.get("acceptance", "[]")),
        "deliverables": parse_bracket_list(fields.get("deliverables", "[]")),
        "evidence": parse_bracket_list(fields.get("evidence", "[]")),
        "due": fields.get("due", ""),
    }


def parse_ac_line(ac_line: str) -> Optional[Dict[str, object]]:
    """EN。"""
    match = re.match(r"^\-\s*\[([ xX])\]\s+\[(AC-\d{3})\]\s+(.*)$", ac_line.strip())
    if not match:
        return None
    name, fields = _parse_kv_tail(match.group(3))
    return {
        "checked": match.group(1).lower() == "x",
        "ac_id": match.group(2),
        "name": name,
        "verify_by": fields.get("verify_by", ""),
        "required_tasks": parse_bracket_list(fields.get("required_tasks", "[]")),
        "required_checks": parse_bracket_list(fields.get("required_checks", "[]")),
        "evidence": parse_bracket_list(fields.get("evidence", "[]")),
    }


def _validate_id_list(items: List[str], pattern: str, label: str, owner_id: str) -> List[str]:
    """EN ID EN。"""
    return [f"{owner_id} {label} invalid: {item}" for item in items if not re.fullmatch(pattern, item)]


def validate_task_line(task_line: str) -> List[str]:
    """EN itemsEN schema EN。"""
    parsed = parse_task_line(task_line)
    if not parsed:
        return [f"ENinvalid: {task_line}"]
    errors: List[str] = []
    task_id = str(parsed["task_id"])
    if parsed["executor"] not in ALLOWED_EXECUTOR:
        errors.append(f"{task_id} executor invalid: {parsed['executor']}")
    due = str(parsed.get("due", "")).strip()
    if due and due not in {"YYYY-MM-DD", "null"} and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", due):
        errors.append(f"{task_id} due ENinvalid: {due}")
    errors.extend(_validate_id_list(parsed["task_depends_on"], r"TASK-\d{3}|TASK-TBD", "task_depends_on", task_id))
    errors.extend(_validate_id_list(parsed["acceptance"], r"AC-\d{3}", "acceptance", task_id))
    return errors


def validate_ac_line(ac_line: str) -> List[str]:
    """EN itemsEN schema EN。"""
    parsed = parse_ac_line(ac_line)
    if not parsed:
        return [f"ENinvalid: {ac_line}"]
    errors: List[str] = []
    ac_id = str(parsed["ac_id"])
    if str(parsed["verify_by"]) not in ALLOWED_VERIFY_BY:
        errors.append(f"{ac_id} verify_by invalid: {parsed['verify_by']}")
    errors.extend(_validate_id_list(parsed["required_tasks"], r"TASK-\d{3}|TASK-TBD", "required_tasks", ac_id))
    return errors


def normalize_backlog_task_line(task_line: str, new_task_id: str) -> str:
    """EN backlog  itemsEN。"""
    raw = task_line.strip()
    if parse_task_line(raw):
        return raw if raw.startswith("- [ ]") else f"- [ ] {raw}"
    raw = re.sub(r"^\-\s*\[[ xX]\]\s*", "", raw).strip()
    match = re.match(r"^\[(P\d+)\]\s+(.*)$", raw)
    if match:
        priority, rest = match.group(1), match.group(2).strip()
    else:
        priority_match = re.search(r"\bpriority=(P\d+)\b", raw)
        priority = priority_match.group(1) if priority_match else "P1"
        rest = raw
    name = rest.split("|")[0].strip()
    return (
        f"- [ ] [{priority}] [{new_task_id}] {name} | owner=unassigned | executor=agent | "
        f"skills=[] | task_depends_on=[] | acceptance=[] | deliverables=[] | evidence=[] | due=YYYY-MM-DD"
    )


def calculate_progress(filepath: str) -> int:
    """ENcheckedEN。"""
    content = read_text(filepath)
    if not content:
        return 0
    marks = []
    for section_no in (4, 5):
        section = find_section_block(content, section_no)
        if section:
            marks.extend(re.findall(r"^\s*(?:-\s*|\d+\.\s*)\[( |x|X)\]", section[3], re.M))
    return int((sum(1 for mark in marks if mark.lower() == "x") / len(marks)) * 100) if marks else 0


def get_project_stats_dict() -> Dict[str, Any]:
    """EN、EN ADR EN，EN dashboard EN heartbeat EN。"""
    ensure_structure()
    done = len(list_md_files(cfg.archive_exec_dir))
    active = len(list_md_files(cfg.stages_exec_dir))
    total_done, total_pending = 0, 0
    total_pending += len(re.findall(r"^\s*-\s*\[ \]", read_text(cfg.backlog_file), re.M))
    _, active_path = resolve_stage_file(None)
    if active_path:
        content = read_text(active_path)
        for section_no in (4, 5):
            section = find_section_block(content, section_no)
            if not section:
                continue
            body = section[3]
            total_done += len(re.findall(r"^\s*(?:-\s*|\d+\.\s*)\[(x|X)\]", body, re.M))
            total_pending += len(re.findall(r"^\s*(?:-\s*|\d+\.\s*)\[ \]", body, re.M))
    return {
        "archived_stages": done,
        "active_stages": active,
        "tasks_done": total_done,
        "tasks_pending": total_pending,
        "adrs": count_adrs_from_index(),
    }


def get_project_stats() -> str:
    """EN。"""
    stats = get_project_stats_dict()
    return (
        f"EN(EN/EN): {stats['archived_stages']}/{stats['active_stages']} | "
        f"EN(EN/EN): {stats['tasks_done']}/{stats['tasks_pending']} | EN: {stats['adrs']}"
    )


def infer_stage_type(content: str) -> str:
    """EN。"""
    text = content.lower()
    impl_words = ["implement", "refactor", "fix", "integrate", "migrate", "replace", "EN", "EN", "EN", "EN", "EN", "EN", "EN"]
    return "implementation" if any(word in text for word in impl_words) else "planning"


def check_section_items(filepath: str, section_no: int, filter_fn: Callable[[str], bool]) -> Tuple[bool, List[str]]:
    """EN section EN itemsEN checklist  itemsEN。"""
    if not os.path.exists(filepath):
        return True, []
    section = find_section_block(read_text(filepath), section_no)
    if not section:
        return True, []
    pending = [line.strip() for line in re.findall(r"^\s*-\s*\[[ xX]\].*$", section[3], re.M) if filter_fn(line)]
    return len(pending) == 0, pending


def get_pending_tasks(filepath: str) -> List[str]:
    """EN。"""
    if not os.path.exists(filepath):
        return []
    section = find_section_block(read_text(filepath), 4)
    if not section:
        return []
    tasks = re.findall(r"^\s*-\s*\[ \]\s+(.*)$", section[3], re.M)
    return sorted(tasks, key=lambda task: int(match.group(1)) if (match := re.search(r"\[P(\d+)\]", task)) else 999)


def clean_summary_text(text: str) -> str:
    """EN，EN。"""
    if not text:
        return "N/A"
    clean = re.sub(
        r"\s+",
        " ",
        re.sub(r"^\s*-\s*(?:###\s*|\[x\]\s*|\[ \]\s*)?", "", text.replace("**", ""), flags=re.M | re.I),
    )
    return clean.strip() or "N/A"


def extract_summary_brief(content: str) -> str:
    """EN section EN。"""
    section = find_section_block(content, 9)
    if not section:
        return "N/A"
    block = section[2] + section[3]
    title = re.search(r"^- ### \[SUMMARY-\d+\] \| \[\d{4}-\d{2}-\d{2}\] \| \[(.*?)\]", block, re.M)
    goal = re.search(r"^\s*- \*\*EN\*\*: (.*)$", block, re.M)
    results = re.findall(r"^\s*-\s*\[x\]\s+(.*)$", block, re.M)
    audit = re.search(r"^\s*- \*\*EN\*\*: (.*)$", block, re.M)

    parts = []
    if title:
        parts.append(title.group(1).strip())
    if goal:
        parts.append(f"EN：{goal.group(1).strip()}")
    if results:
        parts.append("EN：" + "；".join(result.strip() for result in results[:2]))
    if audit:
        parts.append(f"EN：{audit.group(1).strip()}")
    if parts:
        return " | ".join(parts)[:240]

    raw = " ".join(line.strip() for line in block.splitlines() if line.strip() and not line.strip().startswith(("## ", ">")))
    return clean_summary_text(raw)[:240] or "N/A"


def render_log_entry(filepath: str, message: str, task_name: Optional[str] = None,
                     status: str = "in-progress", next_action: Optional[str] = None,
                     blocked_by: Optional[str] = None) -> str:
    """EN itemsEN Markdown EN，EN。"""
    log_id = _next_id(filepath, "LOG-")
    status_text = f"blocked (Blocked by: {blocked_by})" if status == "blocked" and blocked_by else status
    return (
        f"- ### [{log_id}] | [{now_date()}] | [{task_name or 'SYNC'}] | [{get_sys_user()}] | [Ver:{get_git_info()}]\n"
        f"  - **EN**: {status_text}\n"
        f"  - **EN**: {message}\n"
        f"  - **EN**: {next_action or 'TBD'}\n"
    )


def render_adr_entry(adr_id: str, title: str) -> str:
    """EN items ADR EN Markdown EN，EN。"""
    return (
        f"- ### [{adr_id}] | [{now_date()}] | [{title}]\n"
        f"  - **EN/EN**: TBD\n  - **EN**: TBD\n  - **EN**: TBD\n  - **EN/EN**: TBD\n"
    )


def render_summary_entry(filepath: str, name: str, milestone_goal: str,
                         core_results: List[str], change_audit: str, tech_debt: str) -> str:
    """EN itemsEN Markdown EN，EN。"""
    summary_id = _next_id(filepath, "SUMMARY-")
    result_lines = "\n".join(f"    - [x] {item}" for item in core_results) if core_results else "    - [x] TBD"
    return (
        f"- ### [{summary_id}] | [{now_date()}] | [{name}] | [Ver:{get_git_info()}]\n"
        f"  - **EN**: {milestone_goal}\n"
        f"  - **EN**:\n{result_lines}\n"
        f"  - **EN**: {change_audit}\n"
        f"  - **EN/EN**: {tech_debt}\n"
    )
