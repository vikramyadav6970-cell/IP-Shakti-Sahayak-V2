# MVP_SCOPE.md

The locked feature list. Read this before starting or prioritizing any task —
if a task isn't on the MVP list below, it does not get built before the MVP
list is complete, no matter how small it seems. This file exists because the
first full build drifted from intent; it's the guardrail against that
happening again.

## MVP — build this first, and only this, until it's done and working

1. **Landing page → account creation/login required before the chat
   assistant is usable.** Not optional, not a "guest mode" — this is the
   entry flow, build it as part of the MVP, not deferred.
2. Legal dataset — WIPO Lex (filtered subset, see `ai/prompts/phases.md`
   Phase 1) + FSSAI/Drugs Acts + NBA forms.
3. Deployable — actually running, reachable, demoable. Not just "code exists."
4. RAG — citation-grounded retrieval, never an ungrounded LLM answer.
5. India vs. International jurisdiction toggle, **with an explicit
   out-of-scope guardrail**: if India is selected and the question is outside
   India's IP scope, the system says so explicitly and does not attempt an
   answer. It only answers international questions when the user switches the
   toggle. This is a hard behavioral requirement, not a soft preference — test
   it explicitly.
6. **The 3-step guided onboarding flow** (describe product → confirm/correct
   classification with LLM reconciliation → declare intent → LLM
   reformulates for retrieval), not a generic open-ended chat box from
   message one. See `ARCHITECTURE.md` §5 for the exact flow.
7. Mandatory citations on every substantive answer.
8. Minimised hallucination — citation validator, evidence-only prompting,
   abstention when evidence is insufficient.
9. Guardrails (jurisdiction, TKDL-restriction, no-fabrication).
10. Standing "information, not legal advice" disclaimer.
11. Confidence indicator on every answer.
12. Human escalation path when confidence is low.
13. IP-type routing (Patent/Trademark/GI/etc.) combined with the
    formulation-classification flow — classification AND declared intent both
    thread through the rest of the conversation (see `ARCHITECTURE.md` §6).
14. ABS compliance helper — deterministic, no ML dataset (see
    `ARCHITECTURE.md` §7).
15. Multilingual: **English only for now.** Do not build Hindi/Bhashini
    support as part of the MVP — it's explicitly deferred (see below).

## Explicitly deferred — do not start before the MVP list above is done

1. Knowledge graph (Neo4j, multi-hop reasoning).
2. Agentic multi-source orchestration (multi-step query decomposition).
3. Paid-source connectors (logged-in users only).
4. Full multilingual experience (Hindi + others, beyond MVP's English-only).
5. Voice experience.

## Why this file exists

An agent (or a person) picking up a task should be able to check this list
and immediately know whether a proposed piece of work belongs now or later.
If a task description in `<folder>/prompts/phases.md` seems to ask for
something from the deferred list, flag it in that folder's `status.md` rather
than building it — don't let "it would be nice to have" override this lock.

## When the MVP list above is fully done and demoed successfully

Only then move to the deferred list, still one item at a time, still with the
same testing discipline as the MVP tasks (see `ARCHITECTURE.md` §8 and
`AGENT_PROTOCOL.md` for how tasks get verified and how progression works
without needing permission at every step).
