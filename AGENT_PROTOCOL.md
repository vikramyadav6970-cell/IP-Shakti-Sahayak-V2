# AGENT_PROTOCOL.md

How an agent working on this project moves through tasks and phases without
needing permission at every step — and, just as importantly, when it must
stop and ask for help instead of guessing. Read this alongside `process.md`
before starting any task.

## The core loop

For every task in `<folder>/prompts/phases.md`:

1. Do the task.
2. Run its verification steps (every task has one — if a task you're looking
   at doesn't, treat that as a defect in the task definition and write one
   before proceeding, don't skip verification because the prompt forgot to
   ask for it).
3. **If verification passes:** mark the task `[x]` in `process.md` and this
   folder's `status.md`, and move directly to the next task — do not stop to
   ask permission. This is deliberate: the whole point of writing detailed,
   verifiable task prompts is so a human doesn't need to approve every single
   step.
4. **If verification fails:** debug the actual problem and retry. Do not mark
   the task done, do not skip it, and do not move to the next task while this
   one is failing.

## The retry cap — read this before you start debugging anything

Debugging attempts are capped at **3 per task**. This is not arbitrary — an
earlier session on this project hit a real budget-pool exhaustion crash from
an agent burning through context/quota on an open-ended debugging loop. The
cap exists to prevent a repeat of that, and to prevent a subtler failure mode:
an agent under pressure to "make the test pass" weakening or rewriting the
test to match broken behavior, instead of fixing the actual bug. That is
never an acceptable way to get to attempt 1 passing — a test that was
loosened to pass is not a pass.

- **Attempt 1 fails:** read the actual error/output carefully, form a specific
  hypothesis about the cause, fix it, retest.
- **Attempt 2 fails:** the first hypothesis was wrong. Step back — is this
  actually the right task to be debugging, or does the failure indicate a
  problem in an earlier "done" task (a bad assumption that's only surfacing
  now)? Check `status.md` for whether an earlier task's completion is
  actually solid before continuing to iterate on this one.
- **Attempt 3 fails:** STOP. Do not attempt a 4th fix. Mark the task `[!]`
  blocked in `process.md`, write a clear diagnostic note in this folder's
  `status.md` — what was tried, what the actual error/output was each time,
  and your best current hypothesis for the root cause even if unconfirmed —
  and end your turn there. A human needs to look at this, not because you
  failed, but because 3 wrong hypotheses in a row on the same problem is a
  real signal that something outside this task's assumptions is wrong.

This cap applies per-task, not per-conversation — a fresh task starts at
attempt 1 again, even if a previous task in the same session hit the cap.

## Phase-level progression

The same logic extends to whole phases: once every task in a phase is
genuinely `[x]` (verified, not just attempted), move directly into the next
phase's first task without asking — but before doing so, write a short
phase-completion summary in `process.md` under that phase (what was built,
what was verified, any deviations from the original task prompts) so a human
catching up later doesn't have to reconstruct it from a diff. This is
reporting, not requesting permission — you're not waiting for a response
before continuing.

**Exception — always stop and report instead of proceeding, even with
passing tests, when:**
- A task's verification reveals a design assumption from `ARCHITECTURE.md` or
  `MVP_SCOPE.md` is wrong (not just that the code has a bug, but that the
  *plan* was wrong) — this needs a human decision, not a workaround.
- Continuing would touch something explicitly out of scope per
  `MVP_SCOPE.md`'s deferred list.
- You hit the retry cap (see above).
- A task genuinely cannot be verified without a manual/human step (an API key
  that hasn't been provided yet, a judgment call the task prompt flagged as
  needing human sign-off) — mark it `[!]` with what's needed, don't guess and
  mark it `[x]`.

## What "verification passes" actually means

A test passing is not sufficient on its own if the test itself is weak. For
RAG-pipeline tasks specifically: passing a unit test that mocks the retrieval
layer is not the same as confirming the system gives an accurate answer on
real data. Where a task's verification section distinguishes "unit test" from
"manual smoke test on the real running system," both need to actually happen
— don't treat the unit test passing as license to skip the smoke test. This
project's whole premise is that a wrong-but-confident legal answer is worse
than no answer; a green test suite that never touched real retrieved content
doesn't prove that premise holds.

## Logging discipline (this is what makes autonomous progression safe)

Because no human is approving each step in real time, the written record in
`process.md` and each folder's `status.md` is the only way anyone finds out
what actually happened. Every entry — pass or the 3-attempt failure report —
needs to be specific enough that a human reading it cold, days later, can
tell what was done and why, not just that a checkbox changed. "Fixed the
chunker" is not an adequate log entry; "chunker was producing duplicated
heading text as chunk body on Drugs Rules 1945 — root cause was the
breadcrumb-prefix concatenation reusing the same string twice — fixed in
chunker.py's assemble_chunk() — verified via a 200-chunk sample audit,
duplication rate dropped from ~34% to 0%" is.
