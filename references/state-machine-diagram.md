# State Machine Diagram

## The 3-State Machine

```
                         ┌──────────────────────┐
                         │   User sends task    │
                         └──────────┬───────────┘
                                    │
                                    ▼
              ┌─────────────────────────────────────────┐
              │              PLANNING                   │
              │  ───────────────────────────            │
              │  Trigger: state-modifying task          │
              │  Tools:  read-only + agy --print        │
              │  Output: implementation_plan.md         │
              └──────────────────┬──────────────────────┘
                                 │
                                 │  Plan written
                                 ▼
        ┌───────────────────────────────────────────────┐
        │          WAITING_FOR_APPROVAL                 │
        │  ───────────────────────────────             │
        │  Trigger: plan exists, no APPROVE            │
        │  Tools:  same as PLANNING                    │
        │  Action: answer questions, refine plan       │
        │  Exit:   user types APPROVE → EXECUTION     │
        └──────────────────────┬───────────────────────┘
                               │
                               │  APPROVE detected
                               ▼
        ┌───────────────────────────────────────────────┐
        │              EXECUTION                       │
        │  ──────────────────────────                  │
        │  Trigger: user typed APPROVE/APPROVED        │
        │  Tools:  ALL                                 │
        │  Action: task.md → execute → verify → walkth │
        │  Exit:   task complete OR mid-task pivot     │
        └──────────────────────┬───────────────────────┘
                               │
                               │  Mid-task change
                               ▼
        ┌───────────────────────────────────────────────┐
        │  back to PLANNING                            │
        │  (revise plan, request new APPROVE)          │
        └───────────────────────────────────────────────┘
```

## Tool Allowance Matrix

| Tool | PLANNING | WAITING | EXECUTION |
|------|----------|---------|-----------|
| `view_file` / `read_file` | ✅ | ✅ | ✅ |
| `list_dir` / `search_files` | ✅ | ✅ | ✅ |
| `grep_search` | ✅ | ✅ | ✅ |
| `read_url_content` | ✅ | ✅ | ✅ |
| Read-only `terminal` | ✅ | ✅ | ✅ |
| `agy --print` (second opinion) | ✅ | ✅ | ✅ |
| `write_to_file` | ❌ | ❌ | ✅ |
| `replace_file_content` | ❌ | ❌ | ✅ |
| Stateful `run_command` | ❌ | ❌ | ✅ |
| `delegate_task` | ❌ (pure research only) | ❌ | ✅ |
| `cronjob` create/update | ❌ | ❌ | ✅ |

## State Transitions

| From | To | Trigger |
|------|-----|---------|
| (none) | PLANNING | User sends state-modifying task |
| PLANNING | WAITING_FOR_APPROVAL | Plan file written |
| WAITING_FOR_APPROVAL | WAITING_FOR_APPROVAL | User asks questions, plan refined |
| WAITING_FOR_APPROVAL | EXECUTION | User types APPROVE/APPROVED |
| EXECUTION | EXECUTION | Task proceeds normally |
| EXECUTION | PLANNING | Mid-task pivot: scope changes, new requirements |
| EXECUTION | (done) | Task complete, walkthrough.md written |

## Edge Cases

### APPROVE with conditions

User: "APPROVE but use Python instead of Bash"

→ Drop to PLANNING. Revise plan. Request new APPROVE.

### Mid-execution error

User: "That command failed, try again differently"

→ Stay in EXECUTION. Failure recovery is part of the original approved scope.

### Approval words that aren't APPROVE

User: "looks good", "ship it", "do it", "go ahead"

→ NOT APPROVE. Ask: "Type APPROVE to confirm, or describe what to change."

### Typos

User: "Aprrove", "APROVE", "apporved"

→ Intent obvious. Proceed but flag: "Interpreted as APPROVE (typo). If wrong, say STOP."

### Approval in a multi-user thread

Multiple users in the same thread, one types APPROVE, another types "wait":
→ Most recent signal wins. If simultaneous, ask.

### Cron / batch contexts

`skip_context_files=True` AND `load_soul_identity=True`:
→ SOUL.md is still loaded, but the preflight block isn't emitted per turn
   because there's no interactive user. The discipline is bypassed by design.

### Subagent contexts

Subagents run in isolated contexts with no preflight block. The parent
agent's discipline applies at the parent level. Subagents trust the
parent's approval.

## Output Discipline

In PLANNING/WAITING state, your response contains ONLY:

1. The preflight block
2. Tool calls (read-only)
3. Plan file content (written to disk)
4. "Plan written to implementation_plan.md. Awaiting your APPROVE."

You may NOT emit code fences. You may NOT call state-modifying tools.
This is enforced by the validator in `scripts/validate_preflight.py`.