# frontend/coding_conventions.md

Read `/context.md` and `/process.md` before this file. This file governs how code
is written inside `frontend/` specifically. If any instruction here conflicts with
a task prompt, **these conventions win** — a task prompt describes *what*, this
file governs *how*.

## Stack (authoritative — do not substitute without updating this file)

- **React 18** + **Vite** + **TypeScript** (strict mode). Not Next.js — this was an
  explicit product decision, do not reintroduce it.
- **Tailwind CSS** + **shadcn/ui** for components.
- **Zustand** for client/UI state. **TanStack Query** for all server state — never
  hand-roll a `useEffect` + `fetch` + `useState` data-fetching pattern.
- **React Hook Form** + **Zod** for all forms and their validation schemas.
- **React Router** for routing.
- **Recharts** for charts, **Lucide** for icons, **Framer Motion** for animation
  (use sparingly — this is a compliance tool, clarity beats motion).
- **react-i18next** for i18n (English/Hindi from Phase 5).
- Testing: **Vitest** + **React Testing Library** for components with real logic
  (forms, wizards, citation rendering). Pure presentational components don't need
  tests.

## Hard rules

1. **Never build a custom version of something a chosen library already does.** No
   hand-rolled modal/dropdown/toast/date-picker — use shadcn/ui. No hand-rolled
   fetch/cache/retry logic — use TanStack Query. No hand-rolled form validation —
   use Zod schemas. If shadcn/ui doesn't have a primitive you need, compose it from
   Radix (shadcn/ui's base) rather than writing raw DOM/ARIA handling yourself.
2. **No `any`.** Type every API response against a shared `types/` definition that
   matches the backend's Pydantic schema. If the backend contract isn't final yet,
   define the type from the documented contract in `backend/status.md` /
   `process.md` and flag it with a `// TODO(contract): confirm against backend`
   comment — this is the one allowed TODO category, and it must name what it's
   waiting on.
3. **No other TODOs, stubs, or "// implement later" placeholders** left in code
   that is presented as done. If a task is genuinely partial, mark it `[~]` in
   `process.md`/`status.md` with what's left — don't hide it in a code comment.
4. **No console.log left in committed code.** Use a small logger utility if you
   need dev-time diagnostics, gated behind `import.meta.env.DEV`.
5. **Production-grade only:** every screen that fetches data needs a loading
   state, an empty state, and an error state — not just the happy path. Every form
   needs client-side validation feedback. Every async action that can fail (chat
   query, classification submit) needs visible failure handling, not a silent
   swallow.
6. **Component structure:** one component per file, colocated with its own
   `ComponentName.test.tsx` if it has logic worth testing. Shared types in
   `src/types/`, API calls only inside `src/services/`, never inline `fetch`/
   `axios` calls inside components.
7. **Accessibility is not optional.** Every interactive element keyboard-reachable,
   every icon-only button has an `aria-label`, color is never the only signal
   (e.g. confidence badges need text, not just a color chip).
8. **Jurisdiction and disclaimer rules are UI law, not style choices:** any screen
   rendering a substantive answer must (a) visually separate India vs.
   International content if both are present, and (b) show the "information, not
   legal advice" disclaimer. Don't let a new screen skip this because it "seems
   obvious" — check `context.md` §2 before shipping any answer-rendering surface.

## Folder structure

```
frontend/
├── coding_conventions.md
├── status.md
├── prompts/
│   └── phases.md
└── src/
    ├── app/            # routes/pages
    ├── components/     # shared, reusable components (chat/, citations/, classification/, ui/)
    ├── hooks/
    ├── services/        # API clients — the ONLY place fetch/axios is used
    ├── store/            # Zustand stores
    ├── types/            # shared TS types, mirrors backend schemas
    ├── lib/              # utilities (i18n setup, formatters, etc.)
    └── styles/
```

## API contract discipline

The frontend must never guess a backend response shape. Before wiring a real
endpoint:
1. Check `backend/status.md` / `process.md` for the finalized contract.
2. If not finalized, build against a documented mock in
   `src/services/__mocks__/` and note the mock's shape in your own `status.md` so
   backend can match it (or tell you it's changing).

## Definition of done for any frontend task

- Builds with `npm run build` with zero TypeScript errors.
- Zero ESLint errors (config lives at project root once Phase 0 is done).
- Loading/empty/error states present for anything async.
- No console.log, no `any`, no unauthorized TODOs (see rule 2/3 above).
- `status.md` and `process.md` updated.
