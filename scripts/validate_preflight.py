#!/usr/bin/env python3
"""Validate SOUL.md files against the hermes-preflight protocol.

Checks that a SOUL.md file follows the preflight discipline:
  - Preflight block anchor present
  - All 5 required fields present and in correct order
  - APPROVE rule mentions both APPROVE and APPROVED
  - All 3 states named (PLANNING, WAITING_FOR_APPROVAL, EXECUTION)
  - No-tweak clause present

In --strict mode, additionally checks:
  - Persona section heading
  - Communication section heading
  - Delivery checklist with 5+ numbered items

Stdlib only. No external dependencies.

Exit codes:
  0  PASS (or warn-only mode)
  1  One or more validation failures
  2  Invalid arguments (file not found, bad flag, etc.)

Usage:
  validate_preflight.py [--strict|--warn] [--json] PATH...
  validate_preflight.py --help
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import List, Dict, Any


# === What the validator checks ===

PREFLIGHT_ANCHOR = "### 🛡️ HERMES PRE-FLIGHT CHECK"

REQUIRED_FIELDS = [
    "**Current State:**",
    "**Active Goal:**",
    "**Implementation Plan Approved:**",
    "**Permitted Tools for Current State:**",
    "**Target Action This Turn:**",
]

REQUIRED_STATES = ["PLANNING", "WAITING_FOR_APPROVAL", "EXECUTION"]

NO_TWEAK_PATTERNS = [
    r"no[\s-]+tweak",
    r"no such thing as a simple tweak",
]


def _check_protocol_essentials(content: str) -> List[str]:
    """Hard checks: preflight block + state machine + APPROVE rule."""
    errors = []

    # 1. Preflight anchor
    if PREFLIGHT_ANCHOR not in content:
        errors.append(
            f"Missing preflight block anchor: '{PREFLIGHT_ANCHOR}'"
        )
        # If anchor missing, skip field checks (they'd be misleading)
        return errors

    # 2. All 5 fields present + in correct order
    field_positions = []
    for field in REQUIRED_FIELDS:
        if field not in content:
            errors.append(f"Missing required field: {field}")
        else:
            field_positions.append(content.index(field))

    if len(field_positions) == len(REQUIRED_FIELDS):
        if field_positions != sorted(field_positions):
            errors.append(
                "Preflight fields are out of order. Required order: "
                + " → ".join(f.split(":")[0].strip("*") for f in REQUIRED_FIELDS)
            )

    # 3. APPROVE rule must mention both APPROVE and APPROVED
    has_approve = "APPROVE" in content
    has_approved = "APPROVED" in content
    if not has_approve:
        errors.append("Missing 'APPROVE' in critical rule")
    if not has_approved:
        errors.append(
            "Missing 'APPROVED' in critical rule "
            "(the rule must cover both 'APPROVE' and 'APPROVED' tokens)"
        )

    # 4. All 3 states named
    for state in REQUIRED_STATES:
        if state not in content:
            errors.append(f"Missing state name: {state}")

    # 5. No-tweak clause
    if not any(
        re.search(p, content, re.IGNORECASE) for p in NO_TWEAK_PATTERNS
    ):
        errors.append(
            "Missing no-tweak clause "
            "(add a sentence mentioning 'no-tweak' or 'no such thing as a simple tweak')"
        )

    return errors


def _check_methodology_sections(content: str) -> List[str]:
    """Soft checks: persona + communication + delivery checklist. Used by --strict."""
    errors = []

    # Persona heading (matches "Persona", "How I think persona", etc.)
    if not re.search(r"^#+\s+.*[Pp]ersona", content, re.MULTILINE):
        errors.append("Missing 'Persona' section heading")

    # Communication heading (matches "Communication" or "communicate")
    if not re.search(r"^#+\s+.*[Cc]ommunicat", content, re.MULTILINE):
        errors.append("Missing 'Communication' section heading (e.g., '## How I communicate')")

    # Delivery checklist: 5+ numbered items anywhere + the word "DELIVERY" or "Delivery"
    # in the document (matches both "## Delivery Checklist" headings and inline
    # "DELIVERY CHECKLIST (every task, no exceptions)" patterns).
    numbered_items = re.findall(r"^\s*\d+\.", content, re.MULTILINE)
    if len(numbered_items) < 5:
        errors.append(
            f"Delivery checklist should have 5+ numbered items, found {len(numbered_items)}"
        )
    elif not re.search(r"delivery", content, re.IGNORECASE):
        errors.append(
            "Found 5+ numbered items but no 'Delivery' marker. "
            "Add a heading like '## Delivery Checklist' or a phrase like 'DELIVERY CHECKLIST:'."
        )

    return errors


def check_file(path: Path, strict: bool = False) -> Dict[str, Any]:
    """Validate one SOUL.md file. Returns a result dict."""
    if not path.exists():
        return {
            "path": str(path),
            "ok": False,
            "errors": [f"File not found: {path}"],
        }
    if not path.is_file():
        return {
            "path": str(path),
            "ok": False,
            "errors": [f"Not a regular file: {path}"],
        }

    try:
        content = path.read_text(encoding="utf-8")
    except Exception as e:
        return {
            "path": str(path),
            "ok": False,
            "errors": [f"Cannot read file: {e}"],
        }

    errors = _check_protocol_essentials(content)
    if strict:
        errors.extend(_check_methodology_sections(content))

    return {
        "path": str(path),
        "ok": len(errors) == 0,
        "errors": errors,
        "strict": strict,
    }


def format_text_output(results: List[Dict[str, Any]]) -> str:
    """Human-readable output, one block per file."""
    lines = []
    for r in results:
        if r["ok"]:
            marker = "✓" if not r["strict"] else "✓ (strict)"
            lines.append(f"{marker} {r['path']}")
        else:
            lines.append(f"✗ {r['path']}")
            for err in r["errors"]:
                lines.append(f"    - {err}")
    return "\n".join(lines)


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="validate_preflight.py",
        description=(
            "Validate SOUL.md files against the hermes-preflight protocol. "
            "Checks preflight block, state machine, and APPROVE rule."
        ),
        epilog=(
            "Examples:\n"
            "  %(prog)s ~/.hermes/SOUL.md\n"
            "  %(prog)s --strict ~/.hermes/SOUL.md\n"
            "  %(prog)s --warn ~/.hermes/SOUL.md ~/.hermes/profiles/*/SOUL.md\n"
            "  %(prog)s --json ~/.hermes/SOUL.md\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "paths",
        nargs="+",
        help="One or more SOUL.md files to validate",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--strict",
        action="store_true",
        help=(
            "Also check for persona/communication/delivery-checklist sections. "
            "Default is protocol-essentials only (suitable for the minimal template)."
        ),
    )
    mode.add_argument(
        "--warn",
        action="store_true",
        help="Warn-only mode: print errors but exit 0.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output structured JSON (one object per file).",
    )
    args = parser.parse_args(argv)

    if not args.strict and not args.warn:
        args.strict = False  # Default: protocol-essentials only
    # Note: --strict and --warn are mutually exclusive (enforced by argparse)

    results = []
    for p in args.paths:
        path = Path(p).expanduser().resolve()
        results.append(check_file(path, strict=args.strict))

    # Output
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(format_text_output(results))

    # Exit code
    any_failed = any(not r["ok"] for r in results)
    if any_failed and not args.warn:
        return 1
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)