# Changelog

All notable changes to this skill are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/).

## [1.0.0] - 2026-06-18

### Added
- Initial release
- `SKILL.md` — agent-facing protocol documentation
- `references/methodology.md` — design rationale + history
- `references/state-machine-diagram.md` — visual state machine reference
- `templates/SOUL.md` — full methodology template (passes strict validation)
- `templates/SOUL.md.minimal` — preflight + state machine only (no persona)
- `scripts/validate_preflight.py` — stdlib-only linter, 7.8KB
- `scripts/test_validate_preflight.py` — 19-test self-test suite, stdlib unittest

### Validator behavior
- Default mode: checks protocol essentials (preflight block, 5 fields, APPROVE rule, 3 states, no-tweak clause)
- `--strict` mode: additionally checks persona/communication/delivery sections
- `--warn` mode: exit 0 on failures (errors printed)
- `--json` mode: structured output
- Exit codes: 0=ok, 1=fail, 2=invalid args

### Compatibility
- Hermes Agent v0.13.0+
- Python 3.9+ (validator uses stdlib only)
- Works in any profile mode (`~/.hermes/` or `~/.hermes/profiles/<name>/`)

### Provenance
Codified from a working SOUL.md used in production with Hermes Agent since
v0.9.x. The methodology was iteratively refined through real failures:
- An agent that executed without explicit APPROVE
- An agent that emitted code in chat during PLANNING
- An agent that drifted mid-task without checkpointing

This v1.0.0 captures the methodology that prevents all three.