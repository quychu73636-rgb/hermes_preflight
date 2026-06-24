# Changelog

All notable changes to this skill are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/).

## [1.1.0] - 2026-06-24

Initial clean release of the hermes-preflight skill. This is the first
tagged version in the standalone source repo at
`~/projects/hermes-preflight-skill/`.

### Added
- `SKILL.md` — agent-facing protocol documentation (version 1.1.0)
- `references/methodology.md` — design rationale + history
- `references/state-machine-diagram.md` — visual state machine reference
- `templates/SOUL.md` — full methodology template (passes strict validation)
- `templates/SOUL.md.minimal` — preflight + state machine only (no persona)
- `scripts/validate_preflight.py` — stdlib-only linter
- `scripts/test_validate_preflight.py` — 19-test self-test suite, stdlib unittest
- `install.sh` — two-step installer (SOUL.md template + skill dir) + validator run
- `README.md` — install guide + troubleshooting + post-install memory entry recipe
- `LICENSE` — MIT
- `PR_DESCRIPTION.md` — draft PR body for the upstream `NousResearch/hermes-agent` repo

### Fixed
- `README.md` "Differences from the source author's setup": corrected
  memory path from the nonexistent `~/.hermes/agentmemory/` to the actual
  store at `~/.hermes/memories/MEMORY.md` (agent notes) and
  `~/.hermes/memories/USER.md` (user profile). The `agentmemory` MCP
  server is documented as a separate, heavier service stored in
  `~/.hermes/state.db`.
- `README.md` / `install.sh`: replaced passive "accumulates over time"
  wording with the explicit `memory(action='add', target='memory', ...)`
  call that the user must make (the runtime does not auto-accumulate).
- `install.sh` header: "Two-part install" → "Install + verify" (the
  third numbered item is a verification step, not a separate install
  part).
- `install.sh` "Next steps": added a concrete `memory()` call example
  pointing the user at the README's "Recommended post-install memory
  entry" section.

### Validator behavior
- Default mode: checks protocol essentials (preflight block, 5 fields, APPROVE rule, 3 states, no-tweak clause)
- `--strict` mode: additionally checks persona/communication/delivery sections
- `--warn` mode: exit 0 on failures (errors printed to stderr)
- `--json` mode: structured output
- Exit codes: 0=ok, 1=fail, 2=invalid args

### Compatibility
- Hermes Agent v0.13.0+
- Python 3.9+ (validator uses stdlib only)
- Works in any profile mode (`~/.hermes/` or `~/.hermes/profiles/<name>/`)

### Provenance

Codified from a working SOUL.md used in production with Hermes Agent
since v0.9.x. The methodology was iteratively refined through real
failures:
- An agent that executed without explicit APPROVE
- An agent that emitted code in chat during PLANNING
- An agent that drifted mid-task without checkpointing

This v1.1.0 captures the methodology that prevents all three, plus
the documentation fixes that make the install path unambiguous.
