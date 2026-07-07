# LOCALES_REVIEW.md — Latvian UI-chrome review

Status of the Latvian (`lv`) UI strings in `src/i18n/locales/lv/common.json`.

## What this file covers

`lv/common.json` is a **first-pass machine-authored Latvian translation of the UI chrome only**
— buttons, tab names, labels, status text, welcome/auth copy, and the locale switcher. It is the
analogue of `PHASE3_TEST_KINDS.md`: a draft that requires **native-speaker / clinician review
(Marija Rozevska, MD)** via PR before it is considered production-ready, especially for
clinically-adjacent wording (e.g. "anamnēze", "diferenciāldiagnoze", "imūnglobulīni", test
abbreviations like "PAA"/"CRO", genetic-counselling phrasing).

The English catalog (`en/common.json`) is authored verbatim from the existing hardcoded strings;
its values are **byte-identical** to what shipped before i18n, so the existing vitest suite stays
green with `en` as the default/fallback language.

## Hard rule — clinical case content is NOT in these catalogs

The catalogs contain **only UI chrome**. They contain **no clinical case content**:

- parent/patient dialogue, examination findings, lab values and lab tables, tutor evaluation
  prose, hints, and the structured feedback body all come from the **backend**, already localized
  to the attempt's pinned language (`startCaseLocalized(caseId, mode, language)`), per
  `backend/PHASE5_BLUEPRINT.md` §4.
- Clinical content is **clinician-authored** (`case_localizations`, EN-fallback when LV is
  absent — blueprint §7). The AI applies a `language_directive` to clinician-authored prompts; it
  never invents or machine-translates clinical facts. None of that lives in the frontend.

Strings in these catalogs that *look* clinical (e.g. the investigations placeholder
`"e.g. \"CBC, CRP, immunoglobulins, chest X-ray\""`) are **UI affordance examples that already
existed verbatim in the JSX/React chrome**, not case data. They are chrome and are translated as
chrome; the LV examples ("PAA, CRO, imūnglobulīni, …") still need clinician sign-off for accepted
Latvian abbreviations.

## Items needing native-speaker / clinician review

- All `welcome.*`, `auth.*`, `consultation.*`, `investigations.*`, `diagnosis.*`, `feedback.*`,
  `hint.*`, `tutor.*`, `reflectionDone.*`, `chat.*` LV values.
- Clinically-adjacent terms in particular: `welcome.intro`, `welcome.steps.*`,
  `diagnosis.fields.*`, `feedback.scoreDomain.*`, `investigations.orderPlaceholder` /
  `emptyDescExample`, `consultation.summaryPlaceholder` / `diffPlaceholder`.
- The display short codes `locale.en` = "EN" / `locale.lv` = "LV" are intentionally untranslated.

## Phase 6a — educator dashboard (`dashboard.*`) first-pass LV

The `dashboard.*` block (shell / breadcrumb / cohorts / roster / enroll / assignments / staff /
audit / attempts / replay) is **UI chrome only** — cohort/roster/assignment management, enrollment
guidance, and the read-only transcript-review chrome. It contains **no clinical case content**
(case titles, transcript messages, lab tables, and feedback bodies are rendered from the
backend-localized session, not from these keys). All `dashboard.*` LV values are **first-pass
machine-authored** and need native-speaker / clinician review (Marija Rozevska, MD) via PR.

- Terms needing particular review: `dashboard.heroTitle` ("Pasniedzēja panelis"),
  `dashboard.cohorts.*` ("grupa" for cohort), `dashboard.roster.*` ("saraksts"),
  `dashboard.enroll.*` ("reģistrēt"), `dashboard.assignments.*` ("uzdevums"),
  `dashboard.staff.*` ("mācībspēks"), `dashboard.audit.*` ("audita žurnāls").
- `dashboard.replay.tab*` reuse the same emoji idiom as `chat.tab*`; the case mode / locale labels
  shown on attempt cards reuse the existing `chat.modePractice|modeExam|modeReflection` and
  `locale.en|lv` keys (not duplicated).

## Notes on parity / structure

- `feedback.scoreDomain.*` EN values are kept byte-identical to the previous `deCamelCase()`
  output ("history Taking", "test Selection", …) so the `ScoreGrid` test stays green; the LV
  values are first-pass and need review. When no domain key matches, `ScoreGrid` falls back to
  `deCamelCase()`.
- Callouts/empty-states that previously embedded inline `<strong>`/`<br/>`/`<em>` were split into
  adjacent leaf keys (e.g. `welcome.safetyEmoji|safetyStrong|safetyBody`) so the rendered DOM and
  text remain byte-identical in EN.

## Decisions deferred to the backend owner (blueprint §6.2 flag)

The client `*_PROMPT` constants (`SUMMARY_PROMPT`, `DIFFERENTIALS_PROMPT`, `INTERPRET_PROMPT`,
`FINAL_PROMPT` in `App.tsx`) are still passed to `goToSummary` / `proposeDifferentials` /
`interpretResults` / `submitFinal`, because the backend SDL marks `prompt: String!` as **required**
and the frozen contract forbids changing those signatures. The backend builds its own
language-pinned prompt from `attempt.language` (blueprint §4), so the EN constant passed from the
client is effectively ignored server-side. These constants are deliberately **left in English and
not added to the i18n catalogs** — they are not user-visible chrome. Removing them from the
mutation calls is a backend-coordinated change for a later PR, not part of this i18n infra work.

## Phase 6b — Case-authoring UI chrome (LV, needs review)

Added to `dashboard.*` for the staff/admin case-authoring screens. These are **UI chrome only** —
the clinical case content (titles, parent prompts, lab result text, model answers, …) is **data**
authored per-case in the editor, never catalog strings, and is never machine-translated (the
"Copy from EN" button copies EN bytes verbatim for a human to overwrite). First-pass LV for review:

- `dashboard.section.cases` ("Gadījumi") and `dashboard.breadcrumb.cases/editor`
  ("Gadījumi" / "Redaktors") — section switcher + breadcrumb.
- `dashboard.cases.*` — list chrome: `heading`/`intro`, `newCase`, `createHeading`,
  `slugLabel`/`slugPlaceholder`/`createSubmit`, `draftsHeading`/`publishedHeading` and their
  empty-state copy, `versionLabel` ("v{{no}}"), `statusDraft`/`statusPublished`,
  `lvComplete`/`lvMissing`, `untitled`, `edit`.
- `dashboard.cases.editor.*` — editor chrome: scalar labels (`difficulty`/`targetDiagnosis`/`iuis`
  and `difficulty_beg|int|adv`), language-tab labels, `lvUntranslated`, `copyFromEn` ("Kopēt no
  EN"), `tabEdit`/`tabPreview`, every prose-field label (`fieldTitle`, `fieldParentPrompt`,
  `fieldModelGenetic`, `field_redFlags`, `field_keyClues`, `fieldWrongPaths`, …),
  `save`/`saving`/`unsaved`, `publish`/`publishConfirm`/`publishedReadOnly`,
  `discard`/`discardConfirm`.
- `dashboard.cases.lab.*` — lab-data editor chrome: `heading`, `addRow`, `formatHint` (explains
  ↑/↓ and the per-line convention — a hint, **not** a parser), `nameLabel`, `kindLabel`,
  `kind.numeric_panel|imaging|microbiology|genetic|qualitative`, `resultLabel ({{lang}})`,
  remove/confirm copy, and the empty-name / duplicate-name warnings.
- `dashboard.cases.preview.*` — preview-panel section labels (`banner` "not saved; LLM responses
  are not live here", `opening`, `parentPrompt`, `examFindings`, `labData`, `modelAnswers`,
  `keyClues`, `redFlags`).

Clinically-adjacent LV wording to double-check: "diagnoze" forms, "ģenētiskā konsultēšana",
"trauksmes signāli" (red flags), "galvenās norādes" (key clues), and the lab `kind` taxonomy
labels ("Skaitlisks panelis", "Attēldiagnostika", "Mikrobioloģija", "Kvalitatīvs").

## Phase 6c — Cohort analytics dashboard (LV, needs review)

Added to `dashboard.*` for the staff/admin cohort-analytics panel (`CohortAnalyticsPanel`).
UI chrome only — every value rendered against it (counts, completion rate, score bands, case
slugs, wrong-path keys) is computed data from `cohortAnalytics(cohortId)`, never a catalog
string. First-pass LV for review:

- `dashboard.cohort.tabManage` ("Pārvaldīt") / `dashboard.cohort.tabAnalytics` ("Analītika") —
  the in-cohort tab switcher between the management view and the analytics panel.
- `dashboard.analytics.emptyTitle`/`emptyDescription` — friendly empty/low-n state shown when the
  cohort has no attempts yet.
- `dashboard.analytics.completionHeading` ("Pabeigtība"), `completionStat`
  ("Pabeigti {{completed}} no {{total}} mēģinājumiem") — completion section + progress bar caption.
- `dashboard.analytics.scoreHeading` — per-rubric-dimension stacked-bar heading. The rubric
  dimension labels themselves reuse the existing `feedback.scoreDomain.*` catalog (not duplicated).
- `dashboard.analytics.band.*` — score-band legend/segment labels: `Excellent` ("Teicami"),
  `Good` ("Labi"), `Developing` ("Attīstāmi"), `Needs review` ("Jāpārskata"). Keyed by the exact
  EN band strings the backend returns.
- `dashboard.analytics.accuracyHeading`/`accuracyOutcome` and `accuracy.correct|partially_correct|
  incorrect` ("Pareizi" / "Daļēji pareizi" / "Nepareizi") — diagnostic-accuracy table.
- `dashboard.analytics.attemptsPerCaseHeading`/`caseColumn` — attempts-per-case table (case
  titles come from the existing case list, not this catalog).
- `dashboard.analytics.wrongPathHeading`/`wrongPathColumn`/`wrongPathEmpty` — wrong-path-frequency
  table (the wrong-path keys are case data, shown verbatim).
- `dashboard.analytics.count` ("Skaits") — shared numeric-column header.

Clinically-adjacent LV wording to double-check: the score-band scale ("Teicami / Labi / Attīstāmi
/ Jāpārskata") and accuracy terms ("Daļēji pareizi"). These mirror the feedback-report tone and
should match whatever the clinician approved for student-facing feedback bands.
