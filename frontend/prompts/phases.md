# frontend/prompts/phases.md

Each task below is written as a **ready-to-paste prompt** for an AI coding agent
(Claude Code, Cursor, etc.). Give the agent repo access, then paste the task's
prompt block verbatim (the agent is instructed inside the prompt to read the
context files itself). Do tasks in order within a phase; phases may overlap
slightly with backend/AI phases of the same number (they're designed to sync).

Manual/human steps are called out explicitly — an AI agent cannot do these.

---

## Phase 0 — Project setup

### T0.1 — Scaffold the project

**Manual prerequisite:** Node.js 20+ installed on the machine the agent will run
commands on.

**Prompt:**
```
Read /context.md, /process.md, and /frontend/coding_conventions.md in full before
doing anything.

Task: Scaffold a new Vite + React + TypeScript project inside the existing
`frontend/` folder (do not create a nested duplicate folder — the project root
should be `frontend/`). Requirements:

- Vite + React 18 + TypeScript, strict mode enabled in tsconfig.
- ESLint + Prettier configured with sensible defaults for React/TS; no rule
  disables without a comment explaining why.
- Folder structure exactly as documented in frontend/coding_conventions.md
  ("Folder structure" section) — create the empty folders with a `.gitkeep` where
  needed.
- package.json scripts: dev, build, preview, lint, test.
- A basic `App.tsx` that renders "IP-SAKTI Sahayak" so the dev server can be
  verified working.
- A `.env.example` with `VITE_API_BASE_URL=http://localhost:8000` and any other
  env vars you anticipate needing, each with a one-line comment.

Do not add any dependency not listed in frontend/coding_conventions.md's Stack
section without flagging it clearly in your summary and explaining why it's
necessary.

When done: update /frontend/status.md with what was created, and flip T0.1 to [x]
in /process.md under Frontend > Phase 0.
```

### T0.2 — Install and theme Tailwind + shadcn/ui

**Prompt:**
```
Read /context.md and /frontend/coding_conventions.md first.

Task: Install and configure Tailwind CSS and shadcn/ui in the `frontend/` project.

- Set up a design token scale (colors, spacing, radius) appropriate for a serious
  compliance/legal-tech product — clean, trustworthy, not playful. Avoid default
  shadcn "zinc" look without at least picking a considered accent color; document
  your token choices at the top of the relevant CSS/config file in a comment.
- Install the shadcn/ui components we know we'll need soon: button, input, form,
  card, dialog, tabs, badge, separator, dropdown-menu, toast/sonner, skeleton.
- Verify one component (e.g. Button) renders correctly on the placeholder App.tsx.

When done: update /frontend/status.md listing every shadcn component installed,
and flip T0.2 to [x] in /process.md.
```

### T0.3 — Env config, API client, routing skeleton

**Prompt:**
```
Read /context.md, /process.md, and /frontend/coding_conventions.md first.

Task:
1. Set up React Router with a route skeleton for: `/` (landing), `/chat`,
   `/classify`, `/abs`, `/sources`, `/admin`, `/login`. Each route can render a
   placeholder page for now — this is scaffolding, not the real UI (that's later
   phases).
2. Create `src/services/apiClient.ts`: a thin wrapper around fetch (or axios if you
   prefer, but justify the choice in status.md) that reads `VITE_API_BASE_URL`
   from env, attaches auth headers when a token exists (stub the token read from a
   Zustand auth store you also create a skeleton for), and throws typed errors on
   non-2xx responses.
3. Set up TanStack Query's QueryClientProvider at the app root.
4. Set up a base Zustand store structure: `useAuthStore`, `useJurisdictionStore`
   (India/International — this is a core product concept, see context.md §2).

Do not build real UI yet — this task is infrastructure only. Every placeholder page
must still follow the loading/empty/error state rule where applicable (a static
placeholder page doesn't need it, only note where it will apply later).

When done: update /frontend/status.md and flip T0.3 to [x] in /process.md. Also
update the root README.md §5 "Local setup" if any command changed from what's
documented there.
```

---

## Phase 1 — Core shell

### T1.1 — App shell, navigation, disclaimer banner

**Prompt:**
```
Read /context.md (especially §2 hard constraints), /process.md, and
/frontend/coding_conventions.md first.

Task: Build the persistent app shell:
- Header with product name/logo placeholder, nav links to Chat / Classify / ABS /
  Sources / Admin (admin only visible if role check permits — stub the role check
  against useAuthStore for now).
- A standing, non-dismissible (or re-shown-per-session — your call, document which)
  disclaimer banner: "This tool provides information, not legal advice." It must
  appear on every page that can show a substantive answer (chat, classify, abs,
  sources). This is a hard product requirement, not a style nicety — see
  context.md §2 rule 4.
- Footer with basic links (About, placeholder).
- Responsive: usable on mobile widths down to 375px.

When done: update /frontend/status.md and flip T1.1 to [x] in /process.md.
```

### T1.2 — Jurisdiction toggle

**Prompt:**
```
Read /context.md §2 (rule 2 — never conflate jurisdictions) and
/frontend/coding_conventions.md first.

Task: Build the Jurisdiction toggle component and wire it to the
`useJurisdictionStore` created in T0.3.
- Two-state toggle: India (default) / International, persisted in the store (and
  to localStorage so it survives refresh — but never persist anything else
  sensitive to localStorage).
- When International is selected, a secondary select appears for country/authority:
  USA, European Union, UK, Japan, Australia, Canada, UAE, WHO/International, WIPO.
  For the MVP only USA and European Union need to actually route anywhere real
  later — the rest can be present in the UI but are fine to leave functionally
  inert for now (note this clearly in status.md).
- Expose the current jurisdiction via a hook (`useJurisdiction()`) that other
  components (chat, classify) will consume later.
- Place the toggle prominently in the app shell header, not buried in a settings
  page — this is a primary, always-visible control per the product design.

When done: update /frontend/status.md and flip T1.2 to [x] in /process.md.
```

### T1.3 — Landing page

**Prompt:**
```
Read /context.md and /frontend/coding_conventions.md first.

Task: Build the real landing page at `/`:
- Product name + one-line description of what it does (base this on context.md
  §1, keep it accurate — don't oversell it as a legal advice tool).
- A prominent question input that, on submit, navigates to `/chat` with the query
  pre-filled (wire the actual navigation; the chat page itself is built in Phase
  2, so for now it can just land on the Phase-0 placeholder with the query passed
  via router state or a query param).
- Quick-filter chips: Patent / Trademark / GI / ABS / Regulation — clicking one
  should pre-select that intent for the chat page (store it in a way Phase 2's
  chat page can read).
- The jurisdiction toggle from T1.2 visible here too.

When done: update /frontend/status.md and flip T1.3 to [x] in /process.md.
```

---

## Phase 2 — Chat / RAG interface

**Sequencing note:** `MVP_SCOPE.md` requires account creation/login before
the chat assistant is usable at all — this is not optional. **Do Auth UI
(T5.1, currently written up in Phase 5 below) before continuing with this
phase, not after it** — the task content in T5.1 is correct as written, it's
just filed under the wrong phase number in this document. Treat T5.1 as
effectively "T1.4" in execution order, even though it's not renumbered in
this file. If you have capacity to actually renumber this file cleanly,
that's an improvement worth making — just don't build the chat screen gated
behind nothing while auth sits unbuilt in a later phase.


**Before starting this phase**, check `process.md` → Cross-part notes and
`backend/status.md` for whether `POST /api/v1/chat` contract is finalized. If not,
build against the documented mock shape below and flag it.

Expected contract (confirm against backend before final wiring):
```json
// Request
{ "question": "string", "jurisdiction": "INDIA" | "USA" | "EU" | ..., "language": "en" | "hi" }
// Response
{
  "answer": "string (markdown)",
  "confidence": 0.0-1.0,
  "confidence_label": "LOW" | "MEDIUM" | "HIGH",
  "classification": "string | null",
  "citations": [{ "document": "string", "section": "string", "source_url": "string", "jurisdiction": "string" }],
  "requires_human_review": boolean
}
```

### T2.1 — Chat UI

**Prompt:**
```
Read /context.md, /process.md (check the chat API contract status noted above and
in backend/status.md), and /frontend/coding_conventions.md first.

Task: Build the main chat/assistant screen at `/chat`:
- Message list (user + assistant turns), markdown rendering for assistant answers
  (use a markdown renderer, don't hand-roll one — see conventions rule 1).
- Input box with send button, disabled while a request is in flight, with a
  loading indicator on the assistant's turn while waiting.
- Respect the jurisdiction from useJurisdiction() — send it with every query, and
  visibly label which jurisdiction each answer belongs to.
- If a query was pre-filled from the landing page (T1.3) or a quick-filter chip,
  populate the input on mount.
- Full loading/empty/error states per conventions rule 5: empty state before any
  message sent, error state (with retry) if the request fails.
- Use TanStack Query's mutation for the send-message call via
  src/services/chatService.ts — do not inline fetch calls.

If the backend contract isn't finalized yet, implement chatService.ts against the
documented shape above, isolate it behind an interface so swapping the mock for
the real call later is a one-line change, and note this clearly in status.md.

When done: update /frontend/status.md and flip T2.1 to [x] in /process.md.
```

### T2.2 — Citation cards + confidence badge

**Prompt:**
```
Read /context.md §2 (rules 1, 3, 7) and /frontend/coding_conventions.md first.

Task: Build two reusable components:

1. `<CitationCard>` — renders one citation: document title, section/article
   reference, jurisdiction badge, source authority, and an "Open source" link
   (external, opens the source_url). Render as a numbered reference list under an
   assistant answer, matching numbered markers ([1], [2]...) if the answer text
   contains them. If an answer has zero citations, do not silently omit this —
   show an explicit "No authoritative source found for this answer" state instead,
   since per context.md this should trigger low confidence / abstention, not a
   quietly uncited answer.

2. `<ConfidenceBadge>` — shows confidence as both a color-coded chip AND a text
   label (HIGH/MEDIUM/LOW) — never color alone, per accessibility rule in
   conventions. When LOW, render a visible "Human IP facilitator review
   recommended" call-to-action inline (this becomes the escalation entry point
   wired fully in Phase 4 — for now it can navigate to a placeholder `/escalate`
   route or open a stub dialog; note which in status.md).

Wire both into the chat screen from T2.1.

When done: update /frontend/status.md and flip T2.2 to [x] in /process.md.
```

### T2.3 — Finalize chat API wiring

**Prompt:**
```
Read /process.md Cross-part notes and /backend/status.md for the current, real
`/api/v1/chat` contract before starting — if it still isn't finalized, stop and
report that in status.md instead of guessing further.

Task: Replace the mock/interface-isolated chatService.ts from T2.1 with a real
call to the backend endpoint. Handle all backend error shapes (validation errors,
5xx, auth errors) with distinct, user-appropriate messages — not a generic
"Something went wrong" for every case. Add a basic integration test (Vitest +
RTL, with the network call mocked via MSW or similar) covering: successful answer
render, low-confidence escalation prompt render, and error state render.

When done: update /frontend/status.md and flip T2.3 to [x] in /process.md.
```

### T2.4 — Render the jurisdiction out-of-scope guardrail explicitly

**Prompt:**
```
Read /MVP_SCOPE.md item 4 and /ai/prompts/phases.md T4.5 (the backend/AI-side
guardrail this renders) first.

Task: The backend's `/api/v1/chat` response for an out-of-scope question (per
T4.5's jurisdiction gate) needs a distinct visual treatment from a normal
answer — this must not look like a low-confidence answer or an error, it's a
third, distinct state: "this question is outside the selected jurisdiction."
Add a response-type check in chatService.ts / the chat screen: if the backend
signals out-of-scope (confirm the exact response shape against
backend/status.md — coordinate if T4.5/T3.1's contract doesn't yet have a
distinct field for this), render a clear message naming the mismatch (e.g.
"This looks like a question about US patent law — switch to International to
ask it") with a one-click jurisdiction-toggle action, not just prose telling
the user to do it manually.

VERIFICATION: manually test with the same adversarial question set from
ai/prompts/phases.md T4.5's verification section, run through the actual UI —
confirm each out-of-scope case renders the distinct guardrail state (not a
generic answer, not a generic error) and that the one-click toggle actually
switches jurisdiction and allows re-asking.

When done: update /frontend/status.md and flip T2.4 to [x] in /process.md.
```

---

## Phase 3 — Product classification wizard

### T3.1 — Step 1 & 2: describe product, then classify with LLM-assisted reconciliation

**Prompt:**
```
Read /ARCHITECTURE.md §5 (the 3-step onboarding flow — read this carefully,
it's specific) and /frontend/coding_conventions.md first.

Task: Build the guided onboarding flow at `/onboarding` (or as the entry
state of `/chat` before the first message — your call, document which):

STEP 1 — a single free-text input: "Describe your product or write its
formulation." On submit, call the backend (which calls the AI layer's
step-1 suggestion per ai/prompts/phases.md T3.3) and receive a suggested
classification.

STEP 2 — "Classify your product": render all 6 categories as selectable
cards (classical/generic medicine, patent-or-proprietary medicine,
new/non-classical drug, phytopharmaceutical, Ayurveda-Aahar/nutraceutical,
cosmetic), each showing its description and 2-3 example products (confirm
exact copy against backend/status.md once the classification schema is
finalized; use the SIH problem statement's own category definitions as the
default source of truth for descriptions if not yet available). Visually
highlight the LLM's step-1 suggestion, but let the user pick a different
card — this is a confirm-or-correct interaction, not just a display. On
submit, send both the user's choice and the original LLM suggestion to the
backend for reconciliation (ai/prompts/phases.md T3.3's rules engine
produces the final classification) and receive the final result plus
reasoning.

Use React Hook Form + Zod, shared state across the two steps (don't lose
step-1's answer navigating to step 2), progress indicator.

VERIFICATION: manually test a disagreement case (type a description that
would plausibly get one LLM suggestion, then deliberately pick a different
card) and confirm the reconciliation reasoning is actually shown to the user,
not silently discarded.

When done: update /frontend/status.md and flip T3.1 to [x] in /process.md.
```

### T3.2 — Step 3: declare intent, then show the reconciled result

**Prompt:**
```
Read /ARCHITECTURE.md §5 (step 3 specifically) first.

Task: Build STEP 3 — "What do you want to do with the product?" — option
cards: Patent, Research, Sell/Business, AYUSH Application, Export, Other.
On submit, this (plus all prior onboarding context) goes to the backend,
which triggers the AI layer's query reformulation (ai/prompts/phases.md
T3.3b) and the actual retrieval-grounded answer.

Then build the result view shown after all 3 steps complete:
- Final classification and regulatory pathway.
- An "IP protection map": for each IP type (Patent, Trademark, GI, Design,
  Copyright, Trade Secret, Plant Variety) show a relevance indicator, labeled
  **"relevance" or "potential applicability"** — never a percentage chance of
  legal success, don't let a chart component imply that.
- The actual answer to the implicit question raised by the declared intent
  (e.g. Patent intent → lead with patentability/Section 3(p) content), with
  citations per the chat screen's existing citation-card pattern.
- Standing disclaimer visible.

After this initial result, the conversation continues as normal chat —
subsequent messages skip the 3-step onboarding and carry the established
classification + intent forward (this is a backend/AI-layer concern, not
something the frontend needs to re-implement — see backend/prompts/phases.md
and ai/prompts/phases.md T3.5).

When done: update /frontend/status.md and flip T3.2 to [x] in /process.md.
```

---

## Phase 4 — ABS wizard, Source Explorer, Escalation, Dashboard

### T4.1 — ABS compliance wizard

**Prompt:**
```
Read /context.md §5 (ABS/Biological Diversity Act facts) and
/frontend/coding_conventions.md first.

Task: Build `/abs`, a short wizard: does the product use biological resources? →
which ones (reuse the checklist pattern from T3.1's step 4 if it exists, don't
duplicate the component — extract it to a shared component if needed) → origin
(India/other) → purpose (commercial/research) → was research/access already
involved?. On submit, show a result panel: potential ABS relevance (HIGH/MEDIUM/
LOW/NOT APPLICABLE — text label, not color alone), and a numbered "next steps"
list (identify applicable authority, determine approval/intimation requirement,
identify benefit-sharing obligations, preserve source/provenance information).

When done: update /frontend/status.md and flip T4.1 to [x] in /process.md.
```

### T4.2 — Source Explorer

**Prompt:**
```
Read /context.md §2 rule 3 (never fabricate) and /frontend/coding_conventions.md
first.

Task: Build `/sources`, a searchable/browsable list of corpus documents (calls a
backend `/api/v1/sources` or `/api/v1/documents` endpoint — check backend/status.md
for the exact path and shape; isolate behind a service if not finalized). Each
source entry shows: title, jurisdiction, document type (Statute/Rule/Treaty/
Registry record/Case law), issuing authority, version/amendment date, and a link
to the original. Support filtering by jurisdiction and document type. This screen
exists specifically so users (and judges) can verify the system isn't inventing
sources — make that verifiability the design priority over visual polish.

When done: update /frontend/status.md and flip T4.2 to [x] in /process.md.
```

### T4.3 — Human expert escalation

**Prompt:**
```
Read /context.md and /frontend/coding_conventions.md first.

Task: Replace the placeholder escalation entry point from T2.2 with a real flow:
a dialog/page that shows why escalation is suggested (low confidence reason from
the chat/classification response), collects any additional context the user wants
to add, and submits to a backend `/api/v1/expert` endpoint (check backend/status.md
for shape). Show a confirmation state after submission ("Your query has been
flagged for human review — reference #...").

When done: update /frontend/status.md and flip T4.3 to [x] in /process.md.
```

### T4.4 — Admin / IP dashboard

**Prompt:**
```
Read /frontend/coding_conventions.md first.

Task: Build `/admin` (role-gated to ADMIN/CONTENT_MANAGER via useAuthStore — if
the role isn't permitted, show a clear "not authorized" state, don't just 404
silently). Show corpus/health stats pulled from a backend admin endpoint (check
backend/status.md): document count, indexed vs pending, corpus last-updated date,
retrieval accuracy, citation accuracy, abstention rate (these last three come from
the AI layer's evaluation harness — Phase 5 of ai/prompts/phases.md — so may be
unavailable until then; handle that as a normal empty/error state, not a crash).
Use Recharts for any trend visualization.

When done: update /frontend/status.md and flip T4.4 to [x] in /process.md.
```

---

## Phase 5 — Auth, i18n, polish, deploy

### T5.1 — Auth UI

**Manual prerequisite:** none for the UI itself; real auth requires the backend's
Phase 1 JWT implementation to be live.

**Prompt:**
```
Read /backend/status.md for the finalized auth endpoint shapes, then
/frontend/coding_conventions.md.

Task: Build `/login` (and register if the backend supports self-registration —
check backend/status.md) using React Hook Form + Zod, wire to the real auth
endpoints, store the token via useAuthStore (httpOnly cookie if the backend
supports it — preferred over localStorage for the token; note your choice and
reasoning in status.md), and add route guarding so role-gated routes (e.g.
/admin) redirect unauthenticated users to /login.

When done: update /frontend/status.md and flip T5.1 to [x] in /process.md.
```

### T5.2 — Hindi/English i18n

**Manual prerequisite:** Bhashini API key if you want live translation suggestions
during content authoring — not required for static UI string translation, which
can be done manually/by the agent directly.

**Prompt:**
```
Read /frontend/coding_conventions.md first.

Task: Wire up react-i18next with English and Hindi locale files for all static UI
strings (nav, buttons, form labels, disclaimer text, wizard questions). Add a
language switcher in the app shell. This covers UI chrome only — translating
AI-generated answer content is handled by the AI layer (ai/prompts/phases.md
Phase 5), not here. Keep locale JSON files organized by feature
(common.json, chat.json, classify.json, abs.json) rather than one giant file.

When done: update /frontend/status.md and flip T5.2 to [x] in /process.md.
```

### T5.3 — Accessibility + responsive pass

**Prompt:**
```
Read /frontend/coding_conventions.md first.

Task: Full accessibility and responsive audit across every route built so far:
keyboard navigation, aria-labels on icon-only controls, color-contrast check on
all badges/chips, focus states visible, screen-reader sanity check on the chat
message list (assistant messages should be announced as they arrive — consider an
aria-live region), and responsive check down to 375px width on every screen. Fix
what you find; list anything you couldn't fully resolve in status.md with a
reason.

When done: update /frontend/status.md and flip T5.3 to [x] in /process.md.
```

### T5.4 — Deploy

**Manual prerequisite:** a Vercel account (or equivalent) connected to the repo,
and the real backend URL to point `VITE_API_BASE_URL` at in production.

**Prompt:**
```
Task: Prepare the frontend for deployment: verify `npm run build` produces a clean
production bundle, add a `vercel.json` (or equivalent config for whatever host is
chosen — confirm with the human first if not already decided) with correct SPA
rewrite rules for React Router, document the required production env vars in
README.md, and do a final smoke test against the deployed backend URL once the
human has provided it and set it in the hosting dashboard.

When done: update /frontend/status.md, flip T5.4 to [x] in /process.md, and update
README.md §5 with the real deployed URL.
```
