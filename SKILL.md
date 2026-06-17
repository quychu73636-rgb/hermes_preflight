---
name: hermes-preflight
description: 3-state machine discipline for any non-trivial Hermes task — emit the preflight block, gate execution on APPROVE, lint SOUL.md for compliance. Load for any state-modifying task or when training new Hermes instances on the planning protocol.
version: 1.0.0
---

# Hermes Preflight — 3-State Machine Discipline

A reusable pattern for forcing **plan → approve → execute** discipline on any
Hermes Agent instance. The protocol has three parts:

1. **Emit a preflight block** at the start of every response
2. **Gate execution on user APPROVE** — no state changes without explicit go
3. **Lint SOUL.md** against the canonical template to catch malformed blocks

This skill is **portable**: the same discipline works on any Hermes install,
any profile, any platform. The runtime already loads `~/.hermes/SOUL.md` every
turn via `agent/prompt_builder.py:load_soul_md()`. This skill adds the **lint
+ portability layer** so the discipline can be shared.

## When to Use

Load this skill when:

- Starting a **new project** or onboarding a new Hermes instance
- Reviewing **custom SOUL.md files** before they go into production
- **Training a subagent** that needs to follow the same planning discipline
- A user asks "what's the preflight protocol?" or "lint my SOUL.md"
- Debugging a Hermes instance that's **leaking execution before APPROVE**

Do NOT load for:

- Pure read-only Q&A (the block is emitted but the skill isn't needed)
- Single-line edits that genuinely are tweaks — but be careful, see
  [methodology.md](references/methodology.md) "No-Tweak Clause"

## The Preflight Block (canonical)

Emit this **as the first lines of every response**, before any reasoning or
tool calls. Fill the 5 fields dynamically per state.

```
### 🛡️ HERMES PRE-FLIGHT CHECK
- **Current State:** [PLANNING | WAITING_FOR_APPROVAL | EXECUTION]
- **Active Goal:** [Short description of the user request]
- **Implementation Plan Approved:** [YES | NO | N/A (Read-only query)]
- **Permitted Tools for Current State:** [List only the tools allowed right now]
- **Target Action This Turn:** [e.g., "Drafting implementation_plan.md" | "Awaiting approval" | "Executing approved plan"]
```

**Critical rule — re-check at the START of every turn:**

> Has the user explicitly typed `APPROVE` or `APPROVED` in this conversation?
> - **YES** → STATE: EXECUTION. All tools permitted.
> - **NO** → Locked in PLANNING or WAITING_FOR_APPROVAL. Read-only tools only.
>   No `write_to_file`, no code fences, no execution.

Common typos count as APPROVE if intent is unambiguous (e.g., `Aprrove`,
`APROVE`, `apporved`). When in doubt, ask — but don't be pedantic.

## The 3 States

See [state-machine-diagram.md](references/state-machine-diagram.md) for the
full diagram. Quick reference:

| State | Trigger | Permitted Tools | Deliverable |
|-------|---------|-----------------|-------------|
| **PLANNING** | New state-modifying task | Read-only + `agy --print` | Write `implementation_plan.md` |
| **WAITING_FOR_APPROVAL** | Plan exists, no APPROVE | Same as PLANNING | Answer questions, refine plan |
| **EXECUTION** | User typed APPROVE | All tools | Create `task.md`, execute, verify, write `walkthrough.md` |

## Worked Example

```
User: "Set up a new cron job that checks NIO price every 5 minutes"

Turn 1 — PLANNING:
  State: PLANNING
  Tools: view_file, list_dir, grep_search
  Action: Read cron docs, draft plan
  Output: implementation_plan.md + preflight check + "Awaiting APPROVE"

Turn 2 — WAITING_FOR_APPROVAL (user asks "what about DST handling?"):
  State: WAITING_FOR_APPROVAL
  Tools: same as PLANNING
  Action: Update plan to address DST concern
  Output: revised plan + "Awaiting APPROVE"

Turn 3 — EXECUTION (user types "APPROVE"):
  State: EXECUTION
  Tools: ALL
  Action: Create task.md, run `hermes cron create`, verify with `hermes cron list`
  Output: walkthrough.md + brief confirmation
```

## Validator Usage

```
python scripts/validate_preflight.py [--strict|--warn] [--json] PATH...
```

- `--strict` (default): exit 1 on any failure
- `--warn`: exit 0, print warnings to stderr
- `--json`: structured output (one JSON object per file)

Exit codes: 0=ok, 1=fail, 2=invalid args.

## Files

- `references/methodology.md` — Why this design? History, rationale, edge cases
- `references/state-machine-diagram.md` — Visual reference
- `templates/SOUL.md` — Full methodology template (drop into `~/.hermes/`)
- `templates/SOUL.md.minimal` — Just the preflight + state machine
- `scripts/validate_preflight.py` — Lint tool (stdlib only)
- `scripts/test_validate_preflight.py` — Self-test suite
- `README.md` — Install + quick start

## Compatibility

- Hermes Agent v0.13.0+
- Python 3.9+ (for the validator)
- Works in any profile mode (`~/.hermes/` or `~/.hermes/profiles/<name>/`)
- No external dependencies — validator is stdlib only