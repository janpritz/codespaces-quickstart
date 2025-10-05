#!/usr/bin/env python3
"""Deduplicate and merge actions lists.

This script reads:
 - actions/actions.yml       (expects a mapping with key "actions")
 - actions/actions_list.yml  (expects a YAML list)

It will:
 - Report duplicates inside each file
 - Cross-check entries between the two files and remove duplicates that appear in both (prefer entries in actions.yml)
 - Remove duplicate entries while preserving order
 - Create actions/merged_actions.yml containing the union (order: items from actions.yml first, then new items from actions_list.yml that are not present in actions.yml)
 - Overwrite the original files with deduplicated versions (unless run with --dry-run)
 - Append a timestamped run report to actions/merge_report.md (created if missing)

Usage:
  python actions/dedupe_actions.py        # apply changes
  python actions/dedupe_actions.py --dry-run  # only report changes
"""
import argparse
import sys
from pathlib import Path
from datetime import datetime

try:
    import yaml
except Exception as e:
    print("This script requires PyYAML. Install with: pip install pyyaml")
    raise

ACTIONS_YML = Path("domain/actions.yml")
ACTIONS_LIST_YML = Path("imports/actions-list.yml")
MERGED_YML = Path("imports/merged_actions.yml")
MERGE_REPORT = Path("imports/merge_log.md")


def load_yaml(path: Path):
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def write_yaml(path: Path, data):
    with path.open("w", encoding="utf-8") as f:
        # Use safe_dump with pretty formatting
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)


def unique(seq):
    seen = set()
    out = []
    for x in seq:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def append_report(text: str):
    """Append a timestamped report entry to MERGE_REPORT (create file if necessary)."""
    header = f"\n---\nRun at: {datetime.now().isoformat()}\n\n"
    MERGE_REPORT.parent.mkdir(parents=True, exist_ok=True)
    with MERGE_REPORT.open("a", encoding="utf-8") as f:
        f.write(header)
        f.write(text)
        f.write("\n")


def build_summary_text(a_path, list1, dup1, b_path, list2, dup2, cross_dup, merged, dry_run):
    lines = []
    lines.append(f"Source: {a_path}")
    lines.append(f" - items: {len(list1)}")
    lines.append(f" - duplicates inside file: {len(dup1)}")
    if dup1:
        for d in dup1:
            lines.append(f"    - dup: {d}")
    lines.append(f"Source: {b_path}")
    lines.append(f" - items: {len(list2)}")
    lines.append(f" - duplicates inside file: {len(dup2)}")
    if dup2:
        for d in dup2:
            lines.append(f"    - dup: {d}")
    lines.append(f"Cross-file duplicates (present in both files): {len(cross_dup)}")
    if cross_dup:
        for c in sorted(set(cross_dup)):
            lines.append(f"    - cross-dup: {c}")
    lines.append(f"Merged total: {len(merged)}")
    lines.append(f"Dry-run: {bool(dry_run)}")
    return "\n".join(lines)


def main(dry_run=False):
    try:
        a = load_yaml(ACTIONS_YML) or {}
        list1 = a.get("actions", []) if isinstance(a.get("actions", []), list) else []

        b = load_yaml(ACTIONS_LIST_YML)
        if isinstance(b, list):
            list2 = b
        elif isinstance(b, dict) and "actions" in b and isinstance(b["actions"], list):
            list2 = b["actions"]
        else:
            list2 = []

        # internal duplicates
        dup1 = [x for x in set(list1) if list1.count(x) > 1]
        dup2 = [x for x in set(list2) if list2.count(x) > 1]

        # cross-file duplicates: items that appear in both lists
        cross_dup = [x for x in list1 if x in list2]

        # preserve order while deduplicating each file
        u1 = unique(list1)
        u2 = unique(list2)

        # Remove items from actions_list that already exist in actions.yml (cross-check)
        u2_filtered = [x for x in u2 if x not in set(u1)]

        # merged is actions.yml items first, then only the unique items from actions_list that are not in actions.yml
        merged = u1 + u2_filtered

        # Console output
        print("Summary:")
        print(f" - {ACTIONS_YML}: {len(list1)} items, {len(dup1)} duplicate(s) inside file")
        if dup1:
            for d in dup1:
                print("    dup:", d)
        print(f" - {ACTIONS_LIST_YML}: {len(list2)} items, {len(dup2)} duplicate(s) inside file")
        if dup2:
            for d in dup2:
                print("    dup:", d)
        print(f" - Cross-file duplicates (present in both files): {len(cross_dup)}")
        if cross_dup:
            for c in sorted(set(cross_dup)):
                print("    cross-dup:", c)

        summary_text = build_summary_text(ACTIONS_YML, list1, dup1, ACTIONS_LIST_YML, list2, dup2, cross_dup, merged, dry_run)

        if dry_run:
            print("\nDry-run mode: no files will be changed. To apply changes run without --dry-run.")
            append_report("DRY-RUN\n\n" + summary_text)
            return 0

        # Write deduplicated content back
        a_out = {"actions": u1}
        write_yaml(ACTIONS_YML, a_out)
        # write filtered actions_list (remove cross-file duplicates)
        write_yaml(ACTIONS_LIST_YML, u2_filtered)
        write_yaml(MERGED_YML, {"actions": merged})

        print("\nFiles updated:")
        print(f" - Wrote deduplicated {ACTIONS_YML}")
        print(f" - Wrote filtered {ACTIONS_LIST_YML} (removed cross-file duplicates that existed in actions.yml)")
        print(f" - Wrote merged actions to {MERGED_YML}")

        report_text = "SUCCESS\n\n" + summary_text
        if cross_dup:
            report_text += "\n\nRemoved from actions_list.yml (because they exist in actions.yml):\n"
            for c in sorted(set(cross_dup)):
                report_text += f" - {c}\n"

        append_report(report_text)
        return 0
    except Exception as exc:
        err_text = f"FAILURE\n\nError: {exc}\n"
        append_report(err_text)
        print(err_text, file=sys.stderr)
        return 2


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deduplicate and merge actions lists in actions/ directory.")
    parser.add_argument("--dry-run", action="store_true", help="Show what would change without modifying files.")
    args = parser.parse_args()
    sys.exit(main(dry_run=args.dry_run))