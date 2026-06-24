# hermes-preflight

**3-state machine discipline for Hermes Agent: plan → approve → execute.**

A portable, lintable implementation of the preflight protocol — ready to drop
into any Hermes Agent install.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![Hermes v0.13+](https://img.shields.io/badge/hermes-v0.13+-green.svg)](https://github.com/NousResearch/hermes-agent)

## What it does

Forces **plan → approve → execute** discipline on any non-trivial task:

1. **Emit a preflight block** at the start of every response
2. **Gate execution on user APPROVE** — no state changes without explicit go
3. **Lint your SOUL.md** against the canonical protocol

The runtime already loads `~/.hermes/SOUL.md` every turn. This skill adds the
**portability + lint layer** so the discipline is shareable across instances.

## Install

The skill is a **two-part install**: the SOUL.md template gives you the runtime workflow (the 🛡️ block, the APPROVE gate, the state machine); the skill directory gives you the docs + validator. **Do both.**

### Quick install (recommended)

```bash
# Clone
git clone https://github.com/quychu73636-rgb/hermes_preflight.git
cd hermes_preflight

# One-liner: copies SOUL.md template + installs skill + runs validator
bash install.sh

# Restart Hermes (or start a new session) for SOUL.md to take effect
```

### Manual install (step by step)

```bash
# Step 1: Install the SOUL.md template (this is what makes the workflow run)
cp templates/SOUL.md ~/.hermes/SOUL.md

# Step 2: Install the skill (gives you docs + validator)
mkdir -p ~/.hermes/skills/hermes
cp -r . ~/.hermes/skills/hermes/hermes-preflight/

# Step 3: Verify the install
python3 ~/.hermes/skills/hermes/hermes-preflight/scripts/validate_preflight.py ~/.hermes/SOUL.md

# Step 4: Restart Hermes (or start a new session)
```

### From upstream Nous Research hermes-agent (when PR is merged)

```bash
# After PR lands, the skill will be available as:
#   optional-skills/hermes/hermes-preflight/
# Hermes will auto-discover it on next session start.
# The SOUL.md template still needs to be copied manually from this repo
# (or from the upstream skill's templates/ directory).
```

## Differences from the source author's setup

This skill was extracted from a **production SOUL.md** that has been refined through months of real use. That production file includes everything in `templates/SOUL.md` **plus** user-specific customizations that don't belong in a generic template:

- A specific persona voice (e.g. terse, reliability-obsessed, "if-this-then-that" over data dumps)
- Project context (active strategies, account sizes, file paths, verifier preferences)
- Model + TTS + provider preferences
- Communication-style corrections accumulated over many sessions
- Tool quirks and environment-specific gotchas

These live in `~/.hermes/memories/MEMORY.md` (agent's own notes) and `~/.hermes/memories/USER.md` (your profile) — **not** in the SOUL.md template. Installing this skill gives you **the methodology** (preflight protocol, state machine, delivery checklist, no-tweak clause). It does **not** give you **the author's specific context**.

After installing, your agent will follow the same process discipline. It will not know about your trading strategies, your model preferences, or your past corrections. You add those explicitly with `memory(action='add', target='memory', content=...)` — the runtime loads `MEMORY.md` at the top of every turn, so anything you save is recalled automatically. The `agentmemory` MCP server (stored in `~/.hermes/state.db`) is a separate, heavier service for semantic cross-session search and is not part of this skill.

### Recommended post-install memory entry

After install, add this memory entry so your agent knows the skill exists across sessions:

```
memory(
  action='add',
  target='memory',
  content='hermes-preflight skill at ~/.hermes/skills/hermes/hermes-preflight/ '
          '(auto-discovered by Hermes). Validator: scripts/validate_preflight.py '
          '[--strict|--warn|--json]. 3-state machine (PLANNING/WAITING_FOR_APPROVAL/'
          'EXECUTION), APPROVE-gated, no-tweak clause enforced. Plan files: '
          '~/.hermes/plans/<topic>.md. Walkthrough: ~/.hermes/plans/walkthrough-<topic>.md. '
          'Source repo: ~/projects/hermes-preflight-skill/ (v1.1.0).'
)
```

**Bottom line:** the template is a starting point. Customize the Persona / How I think / How I communicate sections of `~/.hermes/SOUL.md` to match your voice. The methodology stays the same; the context is yours.

## Quick start

1. **Lint your current SOUL.md:**
   ```bash
   python3 scripts/validate_preflight.py ~/.hermes/SOUL.md
   ```

2. **If it passes:** you're already compliant. Done.

3. **If it fails:** the output shows what's missing. Either:
   - Add the missing sections manually, or
   - Copy `templates/SOUL.md` over and re-add your custom persona on top

4. **Run the self-test suite:**
   ```bash
   python3 scripts/test_validate_preflight.py
   ```

## Files in this repo

```
.
├── README.md                              # This file
├── LICENSE                                # MIT
├── CHANGELOG.md                           # v1.0.0 release notes
├── .gitignore                             # Python + IDE exclusions
├── SKILL.md                               # Agent-facing protocol
├── references/
│   ├── methodology.md                     # Why 3 states? History + rationale
│   └── state-machine-diagram.md           # ASCII diagram + tool matrix
├── templates/
│   ├── SOUL.md                            # Full methodology template
│   └── SOUL.md.minimal                    # Just preflight + state machine
└── scripts/
    ├── validate_preflight.py              # Lint tool (stdlib only)
    └── test_validate_preflight.py         # 19-test self-test suite
```

## Validator CLI reference

```
validate_preflight.py [--strict|--warn] [--json] PATH...
```

- `--strict`: also check persona/communication/delivery sections
- `--warn`: exit 0 even on failures (warn-only mode)
- `--json`: structured output (one JSON object per file)

Exit codes: 0=ok, 1=fail, 2=invalid args.

### Examples

```bash
# Single file, default mode
python3 scripts/validate_preflight.py ~/.hermes/SOUL.md

# Multiple files, strict mode, fail-on-any
python3 scripts/validate_preflight.py --strict \
    ~/.hermes/SOUL.md ~/.hermes/profiles/*/SOUL.md

# CI-friendly: warn mode, JSON output
python3 scripts/validate_preflight.py --warn --json ~/.hermes/SOUL.md
```

## Compatibility

| Hermes Version | Status |
|----------------|--------|
| v0.13.0+ | ✅ Tested |
| v0.12.x | ⚠️ Should work; not tested |
| < v0.12 | ❌ `load_soul_md()` API may differ |

| Python | Status |
|--------|--------|
| 3.9+ | ✅ Validator uses stdlib only |
| 3.7-3.8 | ⚠️ Should work; not tested |
| < 3.7 | ❌ f-string syntax differences |

## Provenance

This skill is the codified version of a methodology that emerged from months
of working with Hermes Agent in production. The original SOUL.md was
iteratively refined through real failures — see
[`references/methodology.md`](references/methodology.md) for the history.

## Contributing

Issues and PRs welcome. The skill is intentionally minimal:
- 8 files, ~970 lines total
- Zero non-stdlib dependencies
- One validator, one test suite, two templates, two references

If you're extending it:

1. Update `templates/SOUL.md` with the new content
2. Update `scripts/validate_preflight.py` to check for the new field
3. Add a test case in `scripts/test_validate_preflight.py`
4. Update `SKILL.md` and `references/methodology.md`
5. Run the full self-test suite

Don't ship the template change without the validator update — otherwise your
own template will fail validation on the next run.

## License

MIT — see [LICENSE](LICENSE).

## Related

- [Hermes Agent](https://github.com/NousResearch/hermes-agent) — the runtime this skill targets
- [SOUL.md loader source](https://github.com/NousResearch/hermes-agent/blob/main/agent/prompt_builder.py) — `agent/prompt_builder.py:1313`
- [System prompt consumer](https://github.com/NousResearch/hermes-agent/blob/main/agent/system_prompt.py) — `agent/system_prompt.py:60-98`