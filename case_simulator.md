# IEI Clinical Case Simulator

AI-powered chatbot for training medical students in clinical immunology at Rīga Stradiņš University. Students work through simulated parent consultations for inborn errors of immunity (IEI) cases, developing skills in history-taking, investigation ordering, diagnosis, and management.

---

## Files

| File | Purpose |
|---|---|
| `IEI_Chatbot_6.html` | **Deployable artifact.** Standalone single-file HTML app with React loaded via UMD CDN. No build step needed — open in browser or deploy as-is. Uses `React.createElement(...)` syntax throughout. |
| `IEI_Chatbot_v2.jsx` | **Source file.** JSX version, easier to read and edit. Primary edit target. All changes must be mirrored to the HTML file manually. |

**Rule:** Every change made in the JSX must be replicated in the HTML. The JSX uses JSX syntax; the HTML uses `React.createElement(tag, props, ...children)` equivalents.

---

## Cases

| ID | Title | Diagnosis | Difficulty |
|---|---|---|---|
| `xla` | A Boy Who Is Always Getting Pneumonia | X-linked Agammaglobulinaemia (XLA) | Intermediate |
| `cgd` | Emils — A Toddler With Abscesses Everywhere | X-linked Chronic Granulomatous Disease (CGD) | Advanced |
| `pfapa` | A Girl With Predictable Monthly Fevers | PFAPA Syndrome | Intermediate |
| `hies` | A Teenager Whose Eczema Never Responds to Treatment | Hyper-IgE Syndrome (STAT3 LOF) | Advanced |
| `scid` | A Baby With Infections After BCG Vaccination | Artemis-deficient SCID (DCLRE1C) | Advanced |
| `thi` | A Baby Referred for Low IgG | Transient Hypogammaglobulinaemia of Infancy (THI) | Beginner |

---

## Architecture

### State — key variables

```js
phase       // "history" | "summary" | "examination" | "differential" | "tests" | "interpretation" | "final" | "feedback"
screen      // "welcome" | "chat" | "reflection_done"
activeTab   // "consultation" | "investigations" | "diagnosis"
inputMode   // "history" | "summary_input" | "diff_input" | "interp_input"
mode        // "practice" | "exam" | "reflection"
msgs        // single array — all message types
busy        // bool, disables inputs while Claude is responding
interpText  // student's typed interpretation
interpResult // tutor feedback after interpretation (shown inline in investigations tab)
hintPopup   // string | null — shown as centered modal overlay
feedback    // parsed JSON object from final feedback call
```

### Message types

All messages go into one `msgs` array. Filtered into two feeds:

| Type | Feed | Description |
|---|---|---|
| `"parent"` | Consultation | Parent's spoken response |
| `"student"` | Consultation | Student's typed message |
| `"tutor"` | Consultation | Tutor guidance in consultation context |
| `"system"` | Consultation | Opening message, exam findings |
| `"safety"` | Consultation | Safety alerts |
| `"lab"` | Investigations | Formatted lab result table |
| `"lab_note"` | Investigations | Unrecognised test warning, already-ordered note |
| `"lab_tutor"` | Investigations | Tutor guidance triggered by investigation workflow |

```js
const investMsgs = msgs.filter(m => ["lab","lab_note","lab_tutor"].includes(m.type));
const chatMsgs   = msgs.filter(m => !["lab","lab_note","lab_tutor"].includes(m.type));
```

**Rule:** Only parent responses, the system opening message, and physical examination findings go to `"parent"` / `"system"` / `"tutor"` types. Everything triggered by the investigation workflow (genetic testing notes, interpretation prompts, differential feedback, "submit final" prompt) must use `"lab_tutor"`.

### Phase flow

```
history → summary → examination → differential → tests → interpretation → final → feedback
```

Phases advance automatically by student actions. The `phase` state controls which UI elements are visible (e.g., "Interpret results" button only appears at `tests`).

### Tab layout

- **Consultation** — parent chat feed + clinical action buttons
- **Investigations** — lab results feed + test ordering input / interpretation input / tutor nav buttons
- **Final Diagnosis** — blank until ready, then shows the final answer form

### Claude API

```js
callClaude(messages, system, maxTokens)
// → POST https://api.anthropic.com/v1/messages
// Headers: Content-Type, anthropic-version: "2023-06-01", anthropic-dangerous-allow-browser: "true"
// Model: claude-sonnet-4-6
// No x-api-key header — app runs inside a Claude account session
```

### Key functions

| Function | What it does |
|---|---|
| `startCase(c)` | Resets all state, loads selected case, sets opening message |
| `sendMessage()` | Sends student message to parent (Claude), handles exam trigger, nudges |
| `sendTestOrder()` | Parses test names via `TEST_ALIASES`, returns lab results from `labData` |
| `submitSummary()` | Gets tutor feedback on clinical summary, advances to `examination` phase |
| `submitDifferentials()` | Checks against `wrongPaths`, gets tutor feedback, advances to `tests` |
| `submitInterpretation()` | Gets tutor feedback, stores in `interpResult`, shows nav buttons |
| `submitFinalAnswer()` | Calls Claude for structured JSON feedback, sets `phase = "feedback"` |
| `getHint()` | Builds context summary, calls Claude, shows result in `hintPopup` modal |

### Hint popup

`hintPopup` state holds the hint text. Rendered as a `position: "fixed"` centered modal with a `rgba(0,0,0,0.35)` backdrop (`zIndex: 999`). Clicking the backdrop or "Got it" button clears it. Cleared on `startCase`.

### Interpretation flow

1. Student orders ≥2 tests → "Interpret results" button appears in investigations tab
2. Button sets `phase = "interpretation"`, shows textarea in place of test-order input
3. Student submits → `submitInterpretation` calls Claude, stores result in `interpResult`
4. Tutor feedback shown inline with three nav buttons:
   - **Submit final answer** → sets `phase = "final"`, switches to Diagnosis tab
   - **Ask the parent more questions** → switches to Consultation tab
   - **Order more tests** → clears `interpText` + `interpResult`, resets to test-order input

### Final feedback

`submitFinalAnswer` calls Claude with 1500 tokens, extracts JSON with `/\{[\s\S]*\}/` regex (handles markdown code fences and trailing text). Parsed feedback object has: `scores`, `wellDone`, `missing`, `keyClues`, `reasoningPathway`, `management`, `genetics`, `revision`, `action`. Rendered inline in Consultation tab when `phase === "feedback"`.

---

## Test aliases

`TEST_ALIASES` array maps student input strings to canonical `labData` keys via `detectTestsInMessage()` (case-insensitive substring matching). Key entries:

- `"CBC"` — matches "cbc", "full blood count", "fbc", "lymphocyte count", etc.
- `"blood biochemistry"` — matches "biochemistry", "lft", "liver function", "renal function", "urea", "electrolytes", "u&e", etc. (replaces separate LFT + renal entries)
- `"urinalysis"` — matches "urinalysis", "urine", "dipstick", "urine mc&s", etc.
- `"chest X-ray"` — matches "chest xray", "chest x-ray", "chest x ray", "cxr", "cxr chest", "plain chest", etc.
- `"immunoglobulins"` — matches "igg", "iga", "igm", "immunoglobulin", "serum ig", etc.

`labData` keys per case must match the canonical `key` values in `TEST_ALIASES`.

---

## Modes

| Mode | Behaviour |
|---|---|
| `practice` | Full tutor nudges, hints available, physical exam reminder after 5 parent responses |
| `exam` | Minimal nudges, no proactive hints |
| `reflection` | Post-case review with structured reflection questions |
