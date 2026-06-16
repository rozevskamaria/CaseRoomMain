---
name: port-from-source
description: Use when porting any piece of CaseRoom from the canonical JSX source of truth (IEI_Chatbot_v2.jsx) into the new React/TS frontend or the FastAPI/Python backend. Enforces 1:1 logic + clinical-content fidelity and the project's component/styling/test conventions. Invoke for every port task — component extraction, CaseEngine logic, prompts, clinical data, feedback shape.
---

# port-from-source

Porting work on CaseRoom is **translation, not redesign**. The JSX is the law.

## Source of truth
- **`IEI_Chatbot_v2.jsx`** is canonical. `IEI_Chatbot_6.html` is its Sucrase-compiled artifact —
  a runtime reference, not a second source. Always port from the JSX.
- Before porting anything, **read the exact JSX region** you are translating. Do not port from
  memory or from a paraphrase.

## The fidelity rules (do not break)
1. **Replicate logic 1:1.** Test-detection aliases, `isTestOrder` trigger words, `parseLabText`
   splitting, `flagRow` regexes, phase transitions, wrong-path matching, prompt strings,
   `max_tokens`, the feedback JSON shape — all carried over exactly. Same inputs → same outputs.
2. **Replicate oddities.** If the JSX does something surprising, replicate it and document the
   reference in the commit/PR and `refactor.md §4` — **NOT as an inline code comment** (see "no
   comments" below). Do not silently "fix" it. Surface it to the user as a separate question if it
   looks like a real bug.
3. **Never invent clinical content.** Lab values, parent scripts, model answers, key clues, red
   flags, genetic counselling — moved verbatim. No new cases, no edited values, no "rounding".
4. **No new behaviour** unless the user explicitly asked for it as a deliberate change.
5. **Preserve the UI 1:1.** The rendered result must be visually identical to the JSX — layout,
   the `C` colours, spacing, typography, borders, emoji/icons, hover/active states, animations,
   scrolling. Extracting reusable components + CSS Modules is a code-structure change only; output
   stays pixel-identical. Transcribe `C` and inline styles exactly into CSS variables/modules — do
   not reinterpret or restyle. Verify by screenshotting the ported view against the compiled
   `IEI_Chatbot_6.html`. Any visual change needs explicit user sign-off.

## No code comments
Write/port code WITHOUT comments or explanatory docstrings (backend + frontend + config). Code is
self-documenting via naming. Quirks, rationale, and JSX divergences go in commits/PRs and the
markdown docs, never inline.

## Conventions to apply while porting
- **Frontend:** reusable components over copy-paste (`<Message variant>`, `<LabResultTable>`,
  `<Card>`, `<Button>`, `<Badge>`, `<Modal>`, `<TabBar>`). CSS Modules (`*.module.css`); port the
  `C` colour object to CSS custom properties. The ~30 `useState`s become one typed reducer/store
  (the case state machine). TypeScript strict. Apollo for GraphQL data.
- **Backend:** logic goes in `services/` (the `CaseEngine`), never in resolvers. Resolvers/SSE are
  thin. Repositories are the only DB-aware layer.

## Verify parity
- Port pure logic with a **unit test that uses real inputs from the JSX cases** (e.g. feed
  `detectTestsInMessage` the same phrases, assert the same keys). The test passing against
  JSX-derived fixtures is the parity proof.
- When unsure whether something is "logic to replicate" vs "an improvement to propose", default to
  **replicate**, and raise the improvement separately.

## When NOT to use literal replication
Only when the user has explicitly authorised a behavioural change for that specific piece. Then
note in the PR/commit what diverged from the JSX and why.
