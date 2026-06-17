#!/usr/bin/env python3
"""Self-test suite for validate_preflight.py.

Run from the scripts/ directory:
  python3 test_validate_preflight.py

Or with pytest if available:
  pytest test_validate_preflight.py -v

Stdlib only (unittest). No external dependencies.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).parent
VALIDATOR = SCRIPT_DIR / "validate_preflight.py"

# Minimal SOUL.md that satisfies protocol essentials (no persona sections)
GOOD_MINIMAL = """# Hermes Agent — Minimal

## The Pre-Flight Guard

You MUST output the following exact block as the first lines of every response:

```
### 🛡️ HERMES PRE-FLIGHT CHECK
- **Current State:** [PLANNING | WAITING_FOR_APPROVAL | EXECUTION]
- **Active Goal:** [Short description]
- **Implementation Plan Approved:** [YES | NO | N/A]
- **Permitted Tools for Current State:** [List]
- **Target Action This Turn:** [Action]

**CRITICAL RULE:** Has the user typed APPROVE or APPROVED?
- If YES → EXECUTION. Permitted: ALL tools.
- If NO → Locked in PLANNING or WAITING_FOR_APPROVAL.
```

## State Machine

PLANNING, WAITING_FOR_APPROVAL, EXECUTION.

### THE "NO-TWEAK" CLAUSE

There is no such thing as a simple tweak. Any change is a state modification.
"""

# Full methodology SOUL.md (includes persona/communication/delivery)
GOOD_FULL = GOOD_MINIMAL + """

## Persona

A reliability-obsessed assistant. Precise, not warm.

## How I communicate

Concise by default. Verbose when it matters.

## Delivery Checklist

1. Syntax correct
2. Logic sound
3. API verified
4. End-to-end test run
5. Edge cases reviewed
"""


class TestValidatorScript(unittest.TestCase):
    """Test the validator via subprocess (real CLI behavior)."""

    def _run(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(VALIDATOR), *args],
            capture_output=True,
            text=True,
        )

    def _write_temp(self, content: str) -> Path:
        """Write content to a temp file, return the path."""
        f = tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        )
        f.write(content)
        f.close()
        return Path(f.name)

    def test_help_exits_zero(self):
        result = self._run("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("SOUL.md", result.stdout)

    def test_file_not_found(self):
        result = self._run("/nonexistent/path/SOUL.md")
        self.assertEqual(result.returncode, 1)
        self.assertIn("File not found", result.stdout)

    def test_empty_file_fails(self):
        path = self._write_temp("")
        try:
            result = self._run(str(path))
            self.assertEqual(result.returncode, 1)
            self.assertIn("Missing preflight block anchor", result.stdout)
        finally:
            path.unlink()

    def test_minimal_template_passes(self):
        path = self._write_temp(GOOD_MINIMAL)
        try:
            result = self._run(str(path))
            self.assertEqual(
                result.returncode, 0,
                f"Minimal template should pass. Got:\n{result.stdout}"
            )
            self.assertIn("✓", result.stdout)
        finally:
            path.unlink()

    def test_full_template_passes(self):
        path = self._write_temp(GOOD_FULL)
        try:
            result = self._run(str(path))
            self.assertEqual(
                result.returncode, 0,
                f"Full template should pass. Got:\n{result.stdout}"
            )
            self.assertIn("✓", result.stdout)
        finally:
            path.unlink()

    def test_strict_mode_on_minimal_fails(self):
        """Minimal template lacks persona/communication/delivery → strict fails."""
        path = self._write_temp(GOOD_MINIMAL)
        try:
            result = self._run("--strict", str(path))
            self.assertEqual(result.returncode, 1)
            self.assertIn("Persona", result.stdout)
            self.assertIn("Communication", result.stdout)
            self.assertIn("Delivery", result.stdout)
        finally:
            path.unlink()

    def test_strict_mode_on_full_passes(self):
        path = self._write_temp(GOOD_FULL)
        try:
            result = self._run("--strict", str(path))
            self.assertEqual(
                result.returncode, 0,
                f"Full template should pass strict mode. Got:\n{result.stdout}"
            )
            self.assertIn("✓ (strict)", result.stdout)
        finally:
            path.unlink()

    def test_missing_approve_token(self):
        no_approve = GOOD_MINIMAL.replace("APPROVE or APPROVED", "go")
        path = self._write_temp(no_approve)
        try:
            result = self._run(str(path))
            self.assertEqual(result.returncode, 1)
            self.assertIn("APPROVED", result.stdout)
        finally:
            path.unlink()

    def test_missing_no_tweak_clause(self):
        no_tweak = GOOD_MINIMAL.replace(
            "### THE \"NO-TWEAK\" CLAUSE\n\nThere is no such thing as a simple tweak. Any change is a state modification.",
            ""
        )
        path = self._write_temp(no_tweak)
        try:
            result = self._run(str(path))
            self.assertEqual(result.returncode, 1)
            self.assertIn("no-tweak", result.stdout.lower())
        finally:
            path.unlink()

    def test_missing_state(self):
        no_execution = GOOD_MINIMAL.replace("EXECUTION", "RUNNING")
        path = self._write_temp(no_execution)
        try:
            result = self._run(str(path))
            self.assertEqual(result.returncode, 1)
            self.assertIn("EXECUTION", result.stdout)
        finally:
            path.unlink()

    def test_fields_out_of_order(self):
        reordered = """### 🛡️ HERMES PRE-FLIGHT CHECK
- **Active Goal:** x
- **Current State:** y
- **Implementation Plan Approved:** z
- **Permitted Tools for Current State:** w
- **Target Action This Turn:** v

APPROVE APPROVED PLANNING WAITING_FOR_APPROVAL EXECUTION no-tweak
"""
        path = self._write_temp(reordered)
        try:
            result = self._run(str(path))
            self.assertEqual(result.returncode, 1)
            self.assertIn("out of order", result.stdout)
        finally:
            path.unlink()

    def test_warn_mode_exits_zero(self):
        """Even with failures, --warn mode exits 0."""
        path = self._write_temp("")
        try:
            result = self._run("--warn", str(path))
            self.assertEqual(
                result.returncode, 0,
                "Warn mode should exit 0 even on failures"
            )
            self.assertIn("Missing preflight", result.stdout)
        finally:
            path.unlink()

    def test_json_output(self):
        path = self._write_temp(GOOD_MINIMAL)
        try:
            result = self._run("--json", str(path))
            self.assertEqual(result.returncode, 0)
            data = json.loads(result.stdout)
            self.assertIsInstance(data, list)
            self.assertEqual(len(data), 1)
            self.assertTrue(data[0]["ok"])
            self.assertEqual(data[0]["errors"], [])
        finally:
            path.unlink()

    def test_json_output_with_failures(self):
        path = self._write_temp("")
        try:
            result = self._run("--json", str(path))
            self.assertEqual(result.returncode, 1)
            data = json.loads(result.stdout)
            self.assertFalse(data[0]["ok"])
            self.assertGreater(len(data[0]["errors"]), 0)
        finally:
            path.unlink()

    def test_multiple_files(self):
        good_path = self._write_temp(GOOD_MINIMAL)
        bad_path = self._write_temp("")
        try:
            result = self._run(str(good_path), str(bad_path))
            self.assertEqual(result.returncode, 1)
            self.assertIn("✓", result.stdout)
            self.assertIn("✗", result.stdout)
        finally:
            good_path.unlink()
            bad_path.unlink()


class TestValidatorImports(unittest.TestCase):
    """Test the validator's functions directly (faster, no subprocess)."""

    def setUp(self):
        # Import the validator module to test internal functions
        sys.path.insert(0, str(SCRIPT_DIR))
        import importlib
        mod = importlib.import_module("validate_preflight")
        self.mod = mod

    def tearDown(self):
        sys.path.pop(0)

    def test_essential_checks_pass(self):
        errors = self.mod._check_protocol_essentials(GOOD_MINIMAL)
        self.assertEqual(errors, [], f"Got errors: {errors}")

    def test_essential_checks_fail_on_empty(self):
        errors = self.mod._check_protocol_essentials("")
        self.assertGreater(len(errors), 0)

    def test_section_checks_pass_on_full(self):
        errors = self.mod._check_methodology_sections(GOOD_FULL)
        self.assertEqual(errors, [], f"Got errors: {errors}")

    def test_section_checks_fail_on_minimal(self):
        errors = self.mod._check_methodology_sections(GOOD_MINIMAL)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("Persona" in e for e in errors))
        self.assertTrue(any("Communication" in e for e in errors))
        self.assertTrue(any("Delivery" in e for e in errors))


if __name__ == "__main__":
    unittest.main(verbosity=2)