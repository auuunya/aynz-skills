#!/usr/bin/env python3
"""Assemble multi-module VGS spec into a single monolithic spec.

Implements the deep-merge algorithm from references/composition-protocol.md.
Includes cycle detection for inherits_from chains.

Usage:
    python3 scripts/assemble_modules.py spec.md              # prints assembled YAML
    python3 scripts/assemble_modules.py spec.md -o out.md    # writes to file
    python3 scripts/assemble_modules.py spec.md --check-only # only validate assembly, no output
"""
from __future__ import annotations
import argparse, re, sys, yaml, copy
from pathlib import Path
from typing import Any


class AssemblyError(Exception):
    pass


def extract_yaml_blocks(text: str) -> list[dict]:
    """Return list of parsed dicts from fenced YAML blocks."""
    results = []
    for m in re.finditer(r'```yaml\n(.*?)\n```', text, re.S):
        try:
            data = yaml.safe_load(m.group(1))
            if isinstance(data, dict):
                results.append(data)
        except yaml.YAMLError:
            pass
    return results


def detect_cycles(modules: list[dict]) -> list[str]:
    """Detect cycles in inherits_from chains. Returns list of cycle descriptions.

    Uses standard DFS three-color marking:
      - WHITE (unvisited): not in `visited`
      - GRAY (on current path): in `visiting`
      - BLACK (fully explored): in `visited` but not in `visiting`
    """
    mod_map = {m['module_id']: m for m in modules}
    cycles: list[str] = []
    visited: set[str] = set()
    visiting: set[str] = set()

    def _dfs(mid: str, path: list[str]) -> None:
        if mid in visiting:
            cycle_str = ' → '.join(path + [mid])
            cycles.append(cycle_str)
            return
        if mid in visited:
            return  # already fully explored, no cycle through this node
        visiting.add(mid)
        mod = mod_map.get(mid, {})
        inherits = mod.get('inherits_from', [])
        if isinstance(inherits, str):
            inherits = [inherits]
        for parent in inherits:
            parent = parent.strip()
            if parent in mod_map:
                _dfs(parent, path + [parent])
        visiting.discard(mid)
        visited.add(mid)

    for mod in modules:
        mid = mod['module_id']
        if mid not in visited:
            _dfs(mid, [mid])

    return cycles


def resolve_inheritance(modules: list[dict]) -> list[dict]:
    """Resolve inherits_from chains, applying parent defaults to children."""
    mod_map = {m['module_id']: copy.deepcopy(m) for m in modules}
    resolved = set()

    def _resolve(mid: str) -> dict:
        if mid in resolved:
            return mod_map[mid]
        mod = mod_map[mid]
        inherits = mod.get('inherits_from', [])
        if isinstance(inherits, str):
            inherits = [inherits]

        # Merge parent defaults into child
        for parent_id in inherits:
            if parent_id not in mod_map:
                raise AssemblyError(f"module '{mid}' inherits from unknown module '{parent_id}'")
            parent = _resolve(parent_id)
            parent_copy = copy.deepcopy(parent)
            # Remove parent's identity fields
            parent_copy.pop('module_id', None)
            parent_copy.pop('inherits_from', None)
            parent_copy.pop('overrides', None)
            # Deep merge: parent as base, child overrides
            deep_merge(parent_copy, mod)
            mod = parent_copy
            mod['module_id'] = mid

        # Apply overrides
        overrides = mod.pop('overrides', {})
        if isinstance(overrides, dict):
            for path, value in overrides.items():
                _set_nested(mod, path.split('.'), value)

        mod_map[mid] = mod
        resolved.add(mid)
        return mod

    for mid in mod_map:
        _resolve(mid)

    return list(mod_map.values())


def deep_merge(base: dict, override: dict, _depth: int = 0) -> dict:
    """Deep merge override into base (in-place).

    Per composition-protocol.md:
    - dict + dict → recursive merge
    - list + list → id-based dedup append (override items with same id replace base)
    - other → override wins

    Raises AssemblyError if nesting exceeds MAX_DEPTH (500) to prevent RecursionError attacks.
    """
    MAX_DEPTH = 500
    if _depth > MAX_DEPTH:
        raise AssemblyError(f"deep_merge: nesting depth exceeds {MAX_DEPTH} (possible malicious input)")

    for key, val in override.items():
        if key in base:
            if isinstance(base[key], dict) and isinstance(val, dict):
                deep_merge(base[key], val, _depth + 1)
            elif isinstance(base[key], list) and isinstance(val, list):
                # List merge with id-based dedup per protocol §组装算法
                id_index = {
                    item['id']: i for i, item in enumerate(base[key])
                    if isinstance(item, dict) and 'id' in item
                }
                for item in val:
                    if isinstance(item, dict) and 'id' in item and item['id'] in id_index:
                        base[key][id_index[item['id']]] = copy.deepcopy(item)
                    else:
                        base[key].append(copy.deepcopy(item))
            else:
                base[key] = val
        else:
            base[key] = copy.deepcopy(val)
    return base


def _set_nested(d: dict, path: list[str], value: Any) -> None:
    """Set a nested value by dot-path."""
    for part in path[:-1]:
        d = d.setdefault(part, {})
    d[path[-1]] = value


def assemble(spec: dict, *, debug: bool = False, verbose: bool = False) -> dict:
    """Assemble a multi-module spec into a monolithic spec.

    Raises AssemblyError on:
    - Missing module_ids referenced by blocks
    - Cycle in inherits_from
    - Duplicate module_ids
    """
    modules = spec.get('modules', [])
    if not modules:
        raise AssemblyError("no modules found in spec")

    if verbose:
        print(f'VERBOSE: Found {len(modules)} module(s) to assemble', file=sys.stderr)

    # Check duplicate module_ids
    ids = [m.get('module_id') for m in modules]
    dupes = [x for x in ids if ids.count(x) > 1]
    if dupes:
        raise AssemblyError(f"duplicate module_ids: {set(dupes)}")

    if debug:
        print(f'DEBUG: Module IDs: {ids}', file=sys.stderr)

    # Check blocks reference valid modules
    blocks = spec.get('blocks', [])
    block_ids = {b.get('id') for b in blocks if isinstance(b, dict)}
    module_ids = set(ids)
    orphan_blocks = block_ids - module_ids
    if orphan_blocks:
        raise AssemblyError(f"blocks reference unknown modules: {orphan_blocks}")

    if verbose:
        print(f'VERBOSE: Checking for inheritance cycles...', file=sys.stderr)
    # Cycle detection
    cycles = detect_cycles(modules)
    if cycles:
        raise AssemblyError(f"circular inheritance detected: {cycles}")

    if verbose:
        print(f'VERBOSE: Resolving inheritance chains...', file=sys.stderr)
    # Resolve inheritance
    resolved = resolve_inheritance(modules)

    if debug:
        print(f'DEBUG: Resolved {len(resolved)} block(s)', file=sys.stderr)

    # Build assembled spec
    result = copy.deepcopy(spec)
    result.pop('modules', None)
    result.pop('capabilities', None)  # Per protocol §组装算法: strip extension-only fields
    result['blocks'] = resolved  # Assembled modules become blocks

    return result


def main() -> int:
    p = argparse.ArgumentParser(description='Assemble modular VGS specs')
    p.add_argument('path', help='Input .md or .yaml file')
    p.add_argument('-o', '--output', help='Output file')
    p.add_argument('--check-only', action='store_true', help='Only validate, no output')
    p.add_argument('--debug', action='store_true', help='Print debug information')
    p.add_argument('--verbose', action='store_true', help='Print verbose progress information')
    args = p.parse_args()

    path = Path(args.path)
    if not path.exists():
        print(f'ERROR: file not found: {path}', file=sys.stderr)
        return 1

    if args.verbose:
        print(f'VERBOSE: Loading {path}', file=sys.stderr)
    text = path.read_text(encoding='utf-8')
    blocks = extract_yaml_blocks(text)
    if not blocks:
        print('ERROR: no YAML blocks found', file=sys.stderr)
        return 1

    if args.debug:
        print(f'DEBUG: Found {len(blocks)} YAML block(s)', file=sys.stderr)
    data = blocks[0]
    try:
        result = assemble(data, debug=args.debug, verbose=args.verbose)
        print('OK: assembly successful', file=sys.stderr)
    except AssemblyError as e:
        print(f'ERROR: {e}', file=sys.stderr)
        return 1

    if args.check_only:
        return 0

    output_yaml = yaml.dump(result, allow_unicode=True, default_flow_style=False, sort_keys=False)
    if args.output:
        Path(args.output).write_text(output_yaml, encoding='utf-8')
        print(f'OK: written to {args.output}', file=sys.stderr)
    else:
        print(output_yaml)

    return 0


if __name__ == '__main__':
    sys.exit(main())
