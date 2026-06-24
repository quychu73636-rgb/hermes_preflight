# Methodology — Why 3 States?

This document captures the **why** behind the preflight discipline. If you're
just using the protocol, you can skip this — but if you're extending it,
debugging a misalignment, or training a new instance, this is the context.

## The Core Problem

Large language models with tool access have a **leaky execution** problem:

1. User says "set up a cron job"
2. Model interprets as "do it now"
3. Model calls `write_to_file`, `run_command`, etc.
4. Result: state changes happen without explicit checkpoint

This is fine for `ls` or `cat`. It's catastrophic for `rm -rf`, database
migrations, or any irreversible operation.

The 3-state machine is a **forcing function** that requires explicit user
consent before state changes.

## Why Three States (Not Two or Four)?

**Two states (Plan / Execute):** Doesn't capture the "plan exists but user
is reviewing it" middle ground. Forces the model to either do nothing or
act, when often it should be answering questions about the plan.

**Four states (Idle / Plan / Approve / Execute):** Adds a fourth state for
"just chatting." But "idle" is just the absence of any of the other three.
Adding a state that's identical to "no task" is over-modeling.

**Three states (Plan / Wait / Execute):** Captures the actual decision
points without over-modeling. Each state has a clear trigger and clear
output. Transitions are unambiguous.

## Why a Visible Block (Not Just Internal)?

Two reasons:

1. **Transparency for the user.** You always know exactly what state the
   model is in and what it's about to do. No ambiguity about whether
   "thinking about it" is happening vs "about to act."

2. **Self-discipline for the model.** Re-evaluating state every turn — by
   literally writing it down — prevents drift. Without the visible block,
   models tend to drift toward "I'll just do this small thing" over many
   turns until they've made substantial state changes without any
   checkpoint.

The visible block is the **practice**, not the rule. The rule is "re-check
state every turn." The block makes that practice impossible to skip.

## Why Emit It on EVERY Response?

Because state can change between turns. The user might:

- Mid-execution change their mind ("actually use Python, not Bash")
- Ask a question that should drop you back to PLANNING
- Type APPROVE while you're in WAITING_FOR_APPROVAL
- Send a typo you shouldn't treat as APPROVE

If you only emit the block on the first turn, you can't detect these. By
emitting every turn, you:

- Force yourself to re-read the conversation for APPROVE
- Surface the current state to the user
- Create a paper trail of decisions

## The "No-Tweak" Clause

The plan explicitly says: **there is no such thing as a simple tweak.** Any
change to code, configs, or system state is a state modification and MUST
start in STATE: PLANNING. No exceptions.

This clause exists because:

- **Scope creep is invisible.** A "small change" to one file often requires
  changes in 3 other places. By requiring a plan, you catch the cascade.
- **Reversibility is asymmetric.** A 5-line edit can break a production
  system. Plans force you to think about rollback BEFORE the change.
- **User trust requires checkpoint.** If users can't predict when state
  changes happen, they can't review them. Plans restore that.

The clause is annoying. That's the point.

## Common Failure Modes

### 1. "I was just clarifying, not planning"

If you wrote code in your response while in PLANNING state, you FAILED.
Even a "small example" is a code fence. Move it to the plan file or wait
for EXECUTION.

### 2. "I emitted the block but skipped the APPROVE check"

The block is necessary but not sufficient. The actual gate is the
re-evaluation: did the user type APPROVE/APPROVED? If yes, EXECUTION. If
no, locked.

### 3. "I treated `looks-good` as APPROVE"

Approval words vary: `looks good`, `go ahead`, `ship it`, `do it`. These
are NOT APPROVE. They imply approval but they're not the literal token.
The discipline is strict because the cost of false positives (unwanted
state changes) is high.

If the user types a clear approval but not the literal word, ask:
"Type APPROVE to confirm, or just tell me what you'd like to change."

### 4. "I split one task into two without a new plan"

When the user asks for "and also X" mid-execution, the existing plan no
longer covers the work. Drop back to PLANNING, update the plan, request
APPROVE again. This is annoying but correct.

### 5. "I wrote a plan but never created implementation_plan.md"

A plan is a file. If you describe the plan in chat without writing it to
`implementation_plan.md`, you can't link to it later, can't show
progress, and the user can't share it with collaborators.

Always write the plan to disk. The chat is for discussion; the file is the
contract.

## Why a Validator (Not Just Discipline)?

Discipline fails under pressure. When a model is in a long conversation,
hit token limits, or facing a deadline, it shortcuts.

A validator:

- Catches drift before it ships
- Forces the discipline to be **portable** (other instances can lint their
  own SOUL.md)
- Creates a **shared standard** for "what does compliant look like?"
- Makes the discipline **auditable** (you can prove an instance followed it)

The validator is a backup, not the primary mechanism. The primary
mechanism is the model emitting the block on every turn. The validator
catches when the model forgets.

## History of This Methodology

This skill is the codified version of a methodology that emerged from
months of working with Hermes Agent in production. The original SOUL.md
that this skill formalizes was iteratively refined over many sessions:

- **Initial:** Simple "be careful, plan first" guidance
- **v2:** Added 3-state machine + APPROVE rule
- **v3:** Added no-tweak clause + delivery checklist
- **v4 (this skill):** Codified into portable form with lint tool

Each iteration was driven by a real failure: an agent that executed
without approval, an agent that drifted mid-task, an agent that emitted
code in chat before the plan was approved. The validator catches the
pattern at the source.

## When NOT to Use This Skill

There are legitimate cases where the discipline is too heavy:

- **Single-question Q&A** with no state change. Don't emit the block.
- **Batch processing** with `skip_context_files=True`. The discipline is
  bypassed intentionally for data-gen workflows.
- **Cron jobs** that are pre-approved by the user. Cron tasks don't get
  user approval per tick; the whole job was approved at creation.

For all other cases, the discipline is non-negotiable. The cost of
running it (a 6-line block per response) is trivial. The cost of skipping
it (untracked state changes) is unbounded.

## Extending This Skill

If you want to add to the methodology (e.g., a 4-state machine, a new
field in the block, additional validator checks), here's the order:

1. Update `templates/SOUL.md` with the new content
2. Update `scripts/validate_preflight.py` to check for the new field
3. Add a test case in `scripts/test_validate_preflight.py`
4. Update `SKILL.md` and this methodology doc
5. Run the full self-test suite

Don't ship the template change without the validator update — otherwise
your own template will fail validation on the next run.