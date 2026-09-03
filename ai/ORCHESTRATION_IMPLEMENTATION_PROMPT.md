# IP-SAKTI Sahayak — Multi-Agent Orchestration Implementation

## CONTEXT

The system currently runs a single retrieval pass per query: classify intent
→ retrieve (filtered, gated, deduped) → generate grounded answer. This works
well for single-domain questions. Many real questions span multiple domains
at once (e.g. "Can I patent my Ashwagandha formulation and do I need NBA
approval to source it?" touches both `patent_agent` and `biodiversity_agent`
scope). Right now a single retrieval pass under one intent will only surface
evidence for one domain, and the LLM has to either ignore the other half of
the question or answer it ungrounded.

This task adds a lightweight orchestration layer: decompose the query into
per-domain sub-questions, run scoped retrieval for each domain in parallel,
label the evidence by source domain, and have the LLM synthesize a single
answer that explicitly addresses each domain using only that domain's
evidence — extending the existing grounding discipline (partial grounding,
explicit "not in retrieved evidence" admissions) across domains, not just
within one.

**Do not rebuild retrieval, the jurisdiction filter, the relevance gate, the
dedup logic, or the grounding directive — reuse all of it.** This task adds
a decomposition/dispatch/synthesis layer on top of what exists; it is not a
retrieval rewrite.

---

## 1. DECOMPOSER

New module: `ai/src/orchestration/decomposer.py`

- Input: raw user query (+ conversation context/product state JSON, same as
  the existing chat flow already carries).
- Output: a list of `AgentTask` objects, one per relevant `agent_scope`:
  ```python
  @dataclass
  class AgentTask:
      agent_scope: str        # "patent_agent" | "biodiversity_agent" | etc.
      sub_question: str       # the domain-specific slice of the user's query
      jurisdiction: str       # reuse existing jurisdiction classifier output
  ```
- Implementation approach: **extend the existing intent classifier rather
  than building a separate model call.** The current classifier already maps
  a query to one intent (PATENT, ABS, FOOD_REGULATION, TRADEMARK,
  FORMULATION, EXPORT). Change this to return a **list** of
  (intent, confidence) pairs above a threshold (e.g. 0.3), not just the
  top-1. Map each qualifying intent to its corresponding `agent_scope`(s)
  using the existing `INTENT_IP_DOMAINS`/agent_scope mapping already in
  `retriever.py` — do not invent a new mapping table.
- For each qualifying intent, generate a `sub_question`: if the query
  clearly separates by domain (e.g. "and" joining two asks), split it
  directly; otherwise pass the full original query as `sub_question` for
  each task and let each domain's retrieval find what's relevant to its
  own scope. Simpler is better here — don't over-engineer NLP query
  splitting for the first version.
- **Single-domain queries**: if only one intent qualifies (the common case,
  e.g. "what is Section 3(p)"), the decomposer returns a single-item list
  and the system should behave exactly as it does today — no orchestration
  overhead, same latency, same code path underneath. Orchestration is
  additive, not a forced detour for simple queries.

---

## 2. PARALLEL SCOPED RETRIEVAL

Modify `ai/src/retrieval/retriever.py` (or add a thin wrapper) to expose an
async-friendly entry point that:

- Accepts an `AgentTask` and returns its own independently gated, deduped
  evidence set — reuse `retrieve()` exactly as it works today (jurisdiction
  filter, MIN_RELEVANCE_SCORE=0.45, adaptive query anchoring, dedup logic),
  just called once per task instead of once per query.
- In `chat_service.py` (or wherever the current single retrieval call
  lives), when the decomposer returns more than one `AgentTask`, dispatch
  all of them concurrently:
  ```python
  results = await asyncio.gather(*[
      retrieve_for_agent(task) for task in agent_tasks
  ])
  ```
- Each result stays tagged with its originating `agent_scope` — do not
  merge the raw evidence lists into one undifferentiated pile before it
  reaches the LLM. The labeling is what lets the synthesis step reason
  per-domain instead of treating everything as one topic.

---

## 3. EVIDENCE ASSEMBLY FORMAT

Build a structured object to pass into the prompt template, grouped by
domain, e.g.:

```python
{
  "patent_agent": {
      "sub_question": "Can I patent my Ashwagandha formulation?",
      "evidence": [ ...existing RetrievedEvidence objects... ],
      "hits_found": True
  },
  "biodiversity_agent": {
      "sub_question": "Do I need NBA approval to source it?",
      "evidence": [ ...existing RetrievedEvidence objects... ],
      "hits_found": True
  }
}
```

If a domain's retrieval comes back empty (0 hits after the relevance gate),
keep the entry with `"hits_found": False` and an empty evidence list — don't
drop the domain silently. The synthesis prompt needs to know a domain was
asked about but had no grounding, so it can apply the existing
zero-hallucination disclaimer **for that specific domain's portion of the
answer**, while still answering the other domain(s) normally if they have
evidence. This is the multi-domain extension of the partial-grounding
behavior already working for single-domain queries (the Section 3(e) case
where the LLM correctly said "not in retrieved evidence" for just one part
of an answer).

---

## 4. SYNTHESIS PROMPT UPDATE

Update `ai/src/prompts/templates.py`. Add a new prompt path (or extend the
existing `CONSULTATION_SYSTEM_PROMPT`) for the multi-domain case:

```
MULTI-DOMAIN SYNTHESIS DIRECTIVE (used when more than one agent_scope
was dispatched for this query):

You have been given evidence from multiple domain-specific retrieval
agents. Each domain's evidence is labeled and separated. For your
response:

1. Address each domain's sub-question using ONLY that domain's labeled
   evidence. Do not use patent_agent evidence to answer a
   biodiversity_agent question, or vice versa — treat each domain's
   evidence as isolated from the others, the same way India and
   International evidence are kept isolated from each other.
2. If a domain's evidence set has hits_found: False, apply the existing
   ABSENCE OF RETRIEVED STATUTES RULE for that domain's portion of the
   answer specifically — disclaim, use plain-language principles only,
   never invent citations — even if OTHER domains in the same response
   have strong evidence and get a fully grounded answer. Partial
   grounding across domains is expected and correct, not a failure.
3. Structure your response with a clear heading or clear separation per
   domain so the user can see which conclusions rest on which body of
   law (e.g. "Patentability:" / "ABS / Biological Resource Compliance:").
4. All existing rules still apply within each domain's portion: cite only
   what's in that domain's retrieved evidence, no cross-jurisdictional
   transplantation, no fabricated section/law numbers.
```

Keep the existing single-domain `CONSULTATION_SYSTEM_PROMPT` and grounding
rules completely intact and unchanged for the single-agent-task case — this
is an additional directive layered on for the multi-domain case, not a
replacement.

---

## 5. CONFIDENCE SCORING FOR MULTI-DOMAIN RESPONSES

The existing `ConfidenceScorer.calculate_confidence()` currently scores a
single evidence set. For multi-domain responses, compute confidence
**per domain** and surface all of them, plus an overall response confidence
that reflects the weakest domain, not an average that could mask one weak
domain behind one strong one:

```python
{
  "overall_confidence_label": "MEDIUM",  # driven by the weakest domain
  "domain_confidence": {
      "patent_agent": {"score": 0.91, "label": "HIGH"},
      "biodiversity_agent": {"score": 0.38, "label": "LOW",
                              "requires_human_review": True}
  }
}
```

This matters because a strong patent answer next to a weak/ungrounded ABS
answer should not read to the user as uniformly "HIGH confidence" — the
weak domain needs its own visible signal so the escalation path (which
already exists) can trigger correctly for just that portion.

---

## 6. TESTING

Extend `test_grounding_eval_suite.py` with a new test category:

- **Multi-Domain Decomposition**: confirm a query spanning 2+ known
  intents produces the correct set of `AgentTask`s.
- **Multi-Domain Isolation**: confirm patent evidence never appears
  under a biodiversity heading in the response and vice versa (mirrors
  the existing India/International isolation tests — same pattern, new
  axis).
- **Partial Multi-Domain Grounding**: force one domain's retrieval to
  return empty (mock or a genuinely uncovered query) while the other has
  strong evidence; confirm the response is grounded for one domain and
  correctly disclaims for the other in the same response, per Section 3
  above.
- **Single-Domain Regression**: confirm ordinary single-intent queries
  still take the fast single-agent path with no orchestration overhead
  and unchanged output compared to the current system.

Run the full existing suite (`pytest backend/tests`) alongside the new
tests to confirm nothing in the single-domain path regressed.

---

## DELIVERABLE

- `ai/src/orchestration/decomposer.py`
- Updated `retriever.py` with an async-friendly per-task retrieval entry
  point
- Updated `chat_service.py` wiring: decompose → parallel retrieve → labeled
  evidence assembly → synthesis prompt
- Updated `templates.py` with the multi-domain synthesis directive
- Updated `ConfidenceScorer` for per-domain + overall confidence
- New tests in `test_grounding_eval_suite.py`
- A short before/after example in your response: run the Ashwagandha +
  NBA approval query through the new pipeline and show the full labeled
  evidence assembly and final synthesized response, the same way you've
  been verifying every other change in this project.
