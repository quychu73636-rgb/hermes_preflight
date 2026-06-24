# Pull Request Description (draft)

**Title:** `feat(skills): add hermes-preflight — 3-state machine discipline skill (v1.1.0)`

**Branch:** `feat/hermes-preflight-skill` (in your fork of NousResearch/hermes-agent)

---

## Summary

Adds a new optional skill under `optional-skills/hermes/hermes-preflight/` that codifies the **3-state machine discipline** (PLANNING / WAITING_FOR_APPROVAL / EXECUTION) used to gate state changes on explicit user APPROVE.

The skill ships:

- **SKILL.md** — agent-facing protocol documentation
- **references/methodology.md** — design rationale + history
- **references/state-machine-diagram.md** — visual state machine reference
- **templates/SOUL.md** — full methodology template (passes strict validation)
- **templates/SOUL.md.minimal** — preflight + state machine only (no persona)
- **scripts/validate_preflight.py** — stdlib-only linter (default + strict modes)
- **scripts/test_validate_preflight.py** — 19-test self-test suite (passes)

## Why

The runtime already loads `~/.hermes/SOUL.md` every turn via `agent/prompt_builder.py:load_soul_md()` and injects it as the first slot of the system prompt. This skill adds the **portability + lint layer** so the discipline can be shared across instances.

The methodology was iteratively refined through real production failures:

1. An agent that executed without explicit APPROVE
2. An agent that emitted code in chat during PLANNING
3. An agent that drifted mid-task without checkpointing

This v1.1.0 captures the methodology that prevents all three, plus the documentation fixes that make the install path unambiguous (correct memory paths, explicit post-install `memory()` step).

## Verification evidence

**Self-test suite:** 19/19 pass (`python3 scripts/test_validate_preflight.py`)

**End-to-end scenarios** — all 7 match expectations:

| # | File | Mode | Expected | Actual |
|---|------|------|----------|--------|
| 1 | Production `~/.hermes/SOUL.md` (125 lines) | default | PASS | ✓ |
| 2 | Production `~/.hermes/SOUL.md` (125 lines) | strict | PASS | ✓ |
| 3 | Full template (130 lines) | default | PASS | ✓ |
| 4 | Full template (130 lines) | strict | PASS | ✓ |
| 5 | Minimal template (80 lines) | default | PASS | ✓ |
| 6 | Minimal template (80 lines) | strict | FAIL | ✗ (3 missing sections, as designed) |
| 7 | Empty file | default | FAIL | ✗ (no preflight anchor) |

## Compatibility

- Hermes Agent v0.13.0+ (uses `agent/prompt_builder.py:load_soul_md()`)
- Python 3.9+ (validator is stdlib only)
- Works in any profile mode (`~/.hermes/` or `~/.hermes/profiles/<name>/`)
- Zero external dependencies

## Placement

Following the existing `optional-skills/<category>/<skill-name>/` pattern. **Proposed placement:** `optional-skills/autonomous-ai-agents/hermes-preflight/` (closest category for "agent workflow discipline"). Alternative categories considered: `devops` (workflow tooling), `software-development` (coding discipline). Open to maintainer preference.

**Note for the local install path:** Hermes auto-discovers skills at `~/.hermes/skills/<any-category>/<skill-name>/`, so users can install at `~/.hermes/skills/hermes/hermes-preflight/` (as shown in the skill's own README) regardless of upstream category placement.

## Source repo

A standalone canonical source lives at `~/projects/hermes-preflight-skill/` for users who want to vendor the skill without waiting for the optional-skills inclusion.

## Checklist

- [x] Skill follows `optional-skills/` naming convention
- [x] Frontmatter matches existing skills (`name`, `description`, `version`)
- [x] Zero new runtime dependencies
- [x] Self-test suite included
- [x] Documentation references exact runtime source paths
- [x] Tested against production SOUL.md (passes both modes)
- [ ] Updated `optional-skills/README.md` to list this skill (if applicable)

## Risk

This is a documentation + tooling skill. **No runtime code paths change.** If something is wrong, the worst case is the validator rejects a user's SOUL.md — they can still use the runtime directly without this skill installed.

---

## Submission commands

```bash
# 1. Fork NousResearch/hermes-agent on GitHub (web UI)

# 2. Clone your fork
git clone https://github.com/<your-username>/hermes-agent.git
cd hermes-agent

# 3. Add this skill
mkdir -p optional-skills/hermes/hermes-preflight
cp -r /path/to/standalone/repo/* optional-skills/hermes/hermes-preflight/

# 4. Create branch + commit
git checkout -b feat/hermes-preflight-skill
git add optional-skills/hermes/hermes-preflight/
git commit -m "feat(skills): add hermes-preflight — 3-state machine discipline skill"

# 5. Push to your fork
git push origin feat/hermes-preflight-skill

# 6. Open PR (web UI or after installing gh CLI)
gh pr create \
    --repo NousResearch/hermes-agent \
    --title "feat(skills): add hermes-preflight — 3-state machine discipline skill" \
    --body-file /home/aalmamari/projects/hermes-preflight-skill/PR_DESCRIPTION.md
```

Or open the PR directly via the GitHub web UI after pushing.

---

## Files in this PR

| Path | Lines | Purpose |
|------|-------|---------|
| `optional-skills/hermes/hermes-preflight/SKILL.md` | ~150 | Agent-facing protocol |
| `optional-skills/hermes/hermes-preflight/README.md` | ~80 | Install + troubleshooting |
| `optional-skills/hermes/hermes-preflight/CHANGELOG.md` | ~50 | v1.1.0 release notes |
| `optional-skills/hermes/hermes-preflight/LICENSE` | 21 | MIT |
| `optional-skills/hermes/hermes-preflight/.gitignore` | ~40 | Python + IDE |
| `optional-skills/hermes/hermes-preflight/references/methodology.md` | ~120 | Why 3 states? |
| `optional-skills/hermes/hermes-preflight/references/state-machine-diagram.md` | ~60 | ASCII diagram |
| `optional-skills/hermes/hermes-preflight/templates/SOUL.md` | ~130 | Full template |
| `optional-skills/hermes/hermes-preflight/templates/SOUL.md.minimal` | ~80 | Minimal template |
| `optional-skills/hermes/hermes-preflight/scripts/validate_preflight.py` | ~200 | Validator (stdlib) |
| `optional-skills/hermes/hermes-preflight/scripts/test_validate_preflight.py` | ~250 | 19-test suite |

Total: 11 files, ~1,200 lines added. Zero removed (additive only).