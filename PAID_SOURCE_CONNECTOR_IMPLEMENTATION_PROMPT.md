# IP-SAKTI Sahayak — External / Paid-Source Connector Layer

## CONTEXT

The system currently answers entirely from a static, version-tracked
internal corpus (Qdrant). This task adds a separate, pluggable layer for
querying **live external sources** — official/commercial databases that
provide current data your static corpus structurally cannot (application
status lookups, continuously-updated case law, global prior-art searches).

This is architected to support paid/subscription sources generically, but
demoed for now against WIPO PATENTSCOPE's free public search — the same
interface should work unchanged if a paid subscription (WIPO's Web Service
API, Manupatra, PatSnap, etc.) is added later. **Do not hardcode
PATENTSCOPE-specific logic outside its own connector implementation.**

This is additive — do not change the existing Qdrant-based RAG pipeline,
orchestration, or grounding logic. External source results are a distinct,
clearly-labeled evidence type alongside (not replacing) indexed statutory
evidence.

---

## 1. CONNECTOR INTERFACE

New module: `ai/src/connectors/base.py`

```python
class ExternalSourceConnector(ABC):
    name: str                    # e.g. "wipo_patentscope"
    display_name: str            # e.g. "WIPO PATENTSCOPE"
    requires_api_key: bool
    is_paid: bool                # for cost-tracking/UI labeling
    rate_limit_per_minute: int | None

    @abstractmethod
    async def is_available(self) -> bool:
        """Check API key present / service reachable. Never raise —
        return False on any failure so callers can degrade gracefully."""

    @abstractmethod
    async def search(self, query: str, filters: dict) -> list[ExternalHit]:
        """Live search. Must enforce its own timeout (e.g. 8s) and never
        let a slow/failed external call block the rest of the response."""

    @abstractmethod
    async def get_status(self, reference_number: str) -> ExternalStatus | None:
        """Look up a specific application/registration number, if this
        source supports it. Return None if unsupported or not found —
        never fabricate a status."""
```

```python
@dataclass
class ExternalHit:
    source_name: str          # display_name of the connector
    title: str
    reference_number: str | None
    url: str | None
    snippet: str
    retrieved_at: datetime    # ALWAYS stamp — this is live data, not
                               # version-tracked like the internal corpus,
                               # and the user/LLM must know how fresh it is
    is_paid_source: bool
```

---

## 2. FIRST CONNECTOR IMPLEMENTATION — WIPO PATENTSCOPE

`ai/src/connectors/wipo_patentscope.py`

- For now, implement against PATENTSCOPE's free public search interface
  (no API key required for basic search per WIPO's current terms).
- Structure the implementation so swapping in WIPO's official paid Web
  Service API (SOAP-based, subscription-gated) later is a matter of
  changing this one file's internals — the `search()`/`get_status()`
  signatures and the rest of the system must not need to change.
- Respect WIPO's terms of use for the free search interface — reasonable
  request rate, proper user-agent identification, no aggressive scraping
  that could get the integration blocked. If PATENTSCOPE doesn't expose a
  clean queryable endpoint for programmatic use, flag this explicitly
  rather than building a fragile HTML-scraping workaround — a connector
  that breaks silently on every minor site change is worse than no
  connector. Confirm what's actually available before implementing.
- Config: `WIPO_PATENTSCOPE_ENABLED=true/false` in `.env` — connectors
  must be individually toggleable, since not everyone running this system
  will want live external calls active.

---

## 3. ROUTING — WHEN TO USE A CONNECTOR

Add a new lightweight classification signal (not a new full intent
category) that detects when a query needs LIVE data rather than indexed
legal knowledge:

- Patterns indicating live lookup intent: an explicit application/
  registration/serial number, phrases like "current status," "is this
  already registered/filed," "latest," "as of today," "check if."
- When detected, dispatch to the relevant connector(s) **in addition to**
  the existing static retrieval — do not replace static grounding with
  live search; a patentability *analysis* still needs your indexed
  statutory evidence, a live lookup just adds current status on top.
- If no connector is relevant, or all relevant connectors return
  `is_available() == False`, proceed exactly as today — this must be a
  zero-impact no-op for the vast majority of queries that don't need
  live data.

---

## 4. RESULT LABELING — DO NOT LET LIVE DATA BLEND INTO STATUTORY EVIDENCE

This matters as much as the retrieval-isolation work already done for
jurisdiction and multi-agent domains:

- External connector results are passed to the LLM as a clearly separate,
  labeled block: `=== LIVE EXTERNAL SOURCE: WIPO PATENTSCOPE (retrieved
  2026-09-04 14:32 UTC) ===`, distinct from `=== INDEXED STATUTORY
  EVIDENCE ===`.
- Extend the existing grounding directive: the LLM must state clearly in
  its response when a fact comes from a live external lookup versus the
  indexed corpus (e.g. "According to a live PATENTSCOPE search just now,
  ..." vs. citing Section numbers from the indexed Patents Act) — the
  user needs to know which claims are backed by your version-tracked
  corpus and which are a live snapshot that could change.
- In the citation UI, external hits should render with a distinct visual
  treatment (e.g. a "Live" badge with the retrieval timestamp) rather
  than looking identical to an indexed statutory citation.

---

## 5. GRACEFUL DEGRADATION & COST AWARENESS

- Any connector failure (timeout, auth failure, rate limit, service down)
  must degrade to "proceed without this external data" — log it, do not
  fail the whole chat turn, and do not let the LLM pretend it checked a
  live source when the call actually failed.
- If a connector is marked `is_paid: True`, add basic call-count logging
  (even just an append-only log line per call) so usage/cost is visible —
  this matters practically once a real paid subscription is in place,
  since uncontrolled call volume against a per-query-priced API is a real
  cost risk, not just a technical one.
- Respect `rate_limit_per_minute` with a simple in-memory or Redis-backed
  limiter — do not let a burst of user queries exceed what the connector
  can actually sustain.

---

## 6. TESTING

- Connector unit tests with the live call mocked — confirm `search()` and
  `get_status()` handle success, timeout, and malformed-response cases
  without raising.
- Integration test: a live-lookup-intent query correctly triggers the
  connector AND still retrieves static evidence for any statutory
  analysis portion of the same query.
- Regression: confirm ordinary queries with no live-lookup signal are
  completely unaffected — no added latency, no connector calls made.
- Confirm graceful degradation: simulate the connector being unavailable
  (toggle `WIPO_PATENTSCOPE_ENABLED=false` or force a timeout) and confirm
  the response still completes normally, with an honest note that live
  status wasn't available rather than a fabricated answer.

## DELIVERABLE
- `ExternalSourceConnector` base interface + `wipo_patentscope.py`
  implementation
- Live-lookup-intent detection wired into the existing chat/orchestration
  flow, additive only
- Distinct labeling of live vs. indexed evidence in both the LLM prompt
  and the citation UI
- Graceful degradation + basic paid-call usage logging
- Tests covering success, failure, and full regression on unaffected
  queries
