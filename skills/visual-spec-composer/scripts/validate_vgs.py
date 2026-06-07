#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml

TASK_TYPES = {"single_frame", "multi_block", "image_edit"}
INPUT_TYPES = {"text", "image", "mixed"}
COMPOSITION_MODES = {"single_frame", "multi_block", "collage", "split_screen", "image_edit"}
EXECUTION_MODES = {"one_shot", "two_stage", "multi_pass", "brief_only"}
REFERENCE_TYPES = {"style", "composition", "subject", "detail", "constraint"}


def extract_yaml_text(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        return text
    m = re.search(r"```yaml\n(.*?)\n```", text, re.S)
    if m:
        return m.group(1)
    raise ValueError(f"No fenced YAML block found in {path}")


def load_spec(path: Path) -> Dict[str, Any]:
    raw = extract_yaml_text(path)
    data = yaml.safe_load(raw)
    if not isinstance(data, dict):
        raise ValueError("Top-level YAML must be a mapping/object")
    return data


def norm_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def is_ratio(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    return bool(re.fullmatch(r"\d+:\d+|square", value.strip()))


def add(msgs: List[str], level: str, text: str) -> None:
    msgs.append(f"[{level}] {text}")


def validate(data: Dict[str, Any], *, debug: bool = False, verbose: bool = False) -> Tuple[List[str], List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    suggestions: List[str] = []

    if verbose:
        print("[VERBOSE] Starting validation...")
    if debug:
        print(f"[DEBUG] Top-level keys: {list(data.keys())}")

    required_top = ["version", "task", "input_mode", "canvas", "style", "constraints", "generation_policy"]
    for key in required_top:
        if key not in data:
            add(errors, "ERROR", f"Missing top-level field: {key}")

    if errors:
        return errors, warnings, suggestions

    if data.get("version") in (None, ""):
        add(warnings, "WARN", "version is recommended for traceability, e.g. 'canonical'")

    task = data.get("task") or {}
    input_mode = data.get("input_mode") or {}
    canvas = data.get("canvas") or {}
    layout = data.get("layout") or {}
    blocks = norm_list(data.get("blocks"))
    style = data.get("style") or {}
    constraints = data.get("constraints") or {}
    references = norm_list(data.get("references"))
    reference_priority = data.get("reference_priority") or {}
    gp = data.get("generation_policy") or {}
    outputs = data.get("outputs") or {}

    task_type = task.get("task_type")
    input_type = input_mode.get("type")
    composition_mode = canvas.get("composition_mode")
    execution_mode = gp.get("execution_mode")
    block_count = layout.get("block_count")

    if verbose:
        print(f"[VERBOSE] Checking core field values...")
    if debug:
        print(f"[DEBUG] task_type={task_type!r}, input_type={input_type!r}, composition_mode={composition_mode!r}, execution_mode={execution_mode!r}")

    if task_type not in TASK_TYPES:
        add(errors, "ERROR", f"task.task_type must be one of {sorted(TASK_TYPES)}, got {task_type!r}")
    if input_type not in INPUT_TYPES:
        add(errors, "ERROR", f"input_mode.type must be one of {sorted(INPUT_TYPES)}, got {input_type!r}")
    if composition_mode not in COMPOSITION_MODES:
        add(errors, "ERROR", f"canvas.composition_mode must be one of {sorted(COMPOSITION_MODES)}, got {composition_mode!r}")
    if execution_mode not in EXECUTION_MODES:
        add(errors, "ERROR", f"generation_policy.execution_mode must be one of {sorted(EXECUTION_MODES)}, got {execution_mode!r}")

    if not is_ratio(canvas.get("aspect_ratio")):
        add(warnings, "WARN", f"canvas.aspect_ratio should look like '16:9' or 'square', got {canvas.get('aspect_ratio')!r}")

    if isinstance(block_count, int):
        if block_count != len(blocks):
            add(errors, "ERROR", f"layout.block_count={block_count} but blocks has {len(blocks)} item(s)")
    elif block_count is not None:
        add(errors, "ERROR", "layout.block_count must be an integer when present")

    block_ids = []
    hero_count = 0
    if verbose and blocks:
        print(f"[VERBOSE] Validating {len(blocks)} block(s)...")
    for idx, block in enumerate(blocks, start=1):
        if not isinstance(block, dict):
            add(errors, "ERROR", f"blocks[{idx}] must be an object")
            continue
        bid = block.get("id")
        if not bid:
            add(errors, "ERROR", f"blocks[{idx}] missing id")
        else:
            block_ids.append(bid)
        if block.get("role") == "hero":
            hero_count += 1

    if len(set(block_ids)) != len(block_ids):
        add(errors, "ERROR", "Duplicate block ids detected")
    if hero_count > 1:
        add(warnings, "WARN", f"Found {hero_count} hero blocks; ensure clear primary hierarchy")

    if task_type == "multi_block":
        if isinstance(block_count, int) and block_count < 2:
            add(errors, "ERROR", "multi_block requires layout.block_count >= 2")
        if len(blocks) < 2:
            add(errors, "ERROR", "multi_block requires at least 2 blocks")
        if composition_mode not in {"multi_block", "collage", "split_screen"}:
            add(errors, "ERROR", f"multi_block task should use multi_block/collage/split_screen composition, got {composition_mode!r}")

    if task_type == "single_frame":
        if isinstance(block_count, int) and block_count > 1:
            add(warnings, "WARN", "single_frame usually uses 1 block; if intentional, confirm this is not multi_block")
        if composition_mode == "image_edit":
            add(errors, "ERROR", "single_frame task should not use image_edit composition")

    if task_type == "image_edit":
        if input_type not in {"image", "mixed"}:
            add(errors, "ERROR", "image_edit requires input_mode.type to be 'image' or 'mixed'")
        if composition_mode != "image_edit":
            add(errors, "ERROR", "image_edit task should use canvas.composition_mode = image_edit")

    source_images = norm_list(input_mode.get("source_images"))
    if input_type == "text" and source_images:
        add(warnings, "WARN", "input_mode.type is text but source_images is not empty")
    if task_type == "image_edit" and not source_images:
        add(warnings, "WARN", "image_edit usually should provide at least one source image")

    must_have = {str(x).strip().lower() for x in norm_list(constraints.get("must_have")) if str(x).strip()}
    must_avoid = {str(x).strip().lower() for x in norm_list(constraints.get("must_avoid")) if str(x).strip()}
    overlap = must_have & must_avoid
    if overlap:
        add(errors, "ERROR", f"constraints.must_have conflicts with must_avoid: {sorted(overlap)}")

    text_policy = (constraints.get("text_policy") or {}).get("mode")
    if text_policy == "exact_text_required":
        add(suggestions, "SUGGEST", "Exact readable text usually needs post-layout/typesetting instead of pure one-shot generation")

    style_nonempty = sum(1 for key in ["genre", "realism", "palette", "lighting", "texture", "detail_density", "mood", "transition_system"] if style.get(key))
    if style.get("transition_system") and task_type == "single_frame":
        add(warnings, "WARN", "style.transition_system is more typical for multi_block/collage tasks")

    ref_ids = []
    for idx, ref in enumerate(references, start=1):
        if not isinstance(ref, dict):
            add(errors, "ERROR", f"references[{idx}] must be an object")
            continue
        rid = ref.get("id")
        rtype = ref.get("type")
        role = ref.get("role")
        ownership_fields = ((ref.get("ownership") or {}).get("fields")) or []
        if not rid:
            add(errors, "ERROR", f"references[{idx}] missing id")
        else:
            ref_ids.append(rid)
        if rtype not in REFERENCE_TYPES:
            add(errors, "ERROR", f"references[{idx}].type must be one of {sorted(REFERENCE_TYPES)}, got {rtype!r}")
        if not role:
            add(errors, "ERROR", f"references[{idx}] missing role")
        if not ownership_fields:
            add(errors, "ERROR", f"references[{idx}] missing ownership.fields")
        if rtype == "style" and "subject" in ownership_fields:
            add(warnings, "WARN", f"style reference {rid!r} also owns 'subject'; verify this is intentional")
        if rtype == "subject" and any(x in ownership_fields for x in ["palette", "lighting", "mood"]):
            add(warnings, "WARN", f"subject reference {rid!r} also owns style fields; verify this is intentional")
        pr = ref.get("priority")
        if pr is not None and not (isinstance(pr, int) and pr >= 1):
            add(errors, "ERROR", f"references[{idx}].priority should be a positive integer")

    if len(set(ref_ids)) != len(ref_ids):
        add(errors, "ERROR", "Duplicate reference ids detected")

    if references and not reference_priority:
        add(suggestions, "SUGGEST", "Multiple references work better with explicit reference_priority")
    for field, rid in reference_priority.items():
        if rid and rid not in ref_ids:
            add(errors, "ERROR", f"reference_priority.{field} points to missing reference id {rid!r}")

    small_model_mode = bool(gp.get("small_model_mode"))
    if small_model_mode:
        views = set(norm_list(outputs.get("render_views")))
        if "compact" not in views:
            add(warnings, "WARN", "small_model_mode=true but outputs.render_views does not include 'compact'")
        if style_nonempty > 5:
            add(warnings, "WARN", f"small_model_mode=true but style has {style_nonempty} populated dimensions; consider collapsing")
        if isinstance(block_count, int) and block_count > 4:
            add(warnings, "WARN", "small_model_mode=true with block_count > 4; prefer two_stage or blockwise generation")

    if execution_mode == "one_shot" and isinstance(block_count, int) and block_count > 4:
        add(warnings, "WARN", "one_shot with more than 4 blocks is high risk")
    if execution_mode == "one_shot" and isinstance(block_count, int) and block_count > 6:
        add(warnings, "WARN", "one_shot with more than 6 blocks is strongly discouraged")

    brand_constraints = norm_list(constraints.get("brand_constraints"))
    for idx, bc in enumerate(brand_constraints, start=1):
        if isinstance(bc, dict):
            for must in ["id", "type", "mode", "priority", "apply_to", "value"]:
                if must not in bc:
                    add(warnings, "WARN", f"brand_constraints[{idx}] missing recommended field {must!r}")
        elif not isinstance(bc, str):
            add(warnings, "WARN", f"brand_constraints[{idx}] should be object or string")

    if not warnings and not suggestions:
        add(suggestions, "SUGGEST", "Spec looks structurally healthy")

    return errors, warnings, suggestions


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a VGS YAML file or fenced YAML block in Markdown")
    parser.add_argument("paths", nargs="+", help=".yaml/.yml or .md files")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as non-zero exit")
    parser.add_argument("--debug", action="store_true", help="Print debug information (internal state)")
    parser.add_argument("--verbose", action="store_true", help="Print verbose progress information")
    args = parser.parse_args()

    overall_errors = 0
    overall_warnings = 0

    for raw_path in args.paths:
        path = Path(raw_path)
        print(f"== {path} ==")
        try:
            data = load_spec(path)
            errors, warnings, suggestions = validate(data, debug=args.debug, verbose=args.verbose)
            for line in errors + warnings + suggestions:
                print(line)
            if not (errors or warnings or suggestions):
                print("[SUGGEST] No findings")
            print(f"Summary: {len(errors)} error(s), {len(warnings)} warning(s), {len(suggestions)} suggestion(s)")
            overall_errors += len(errors)
            overall_warnings += len(warnings)
        except Exception as e:
            overall_errors += 1
            print(f"[ERROR] {type(e).__name__}: {e}")
        print()

    if overall_errors > 0:
        return 1
    if args.strict and overall_warnings > 0:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
