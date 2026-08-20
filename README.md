# CaseRoom — IEI Clinical Case Simulator

**An AI-powered clinical case simulator for teaching Inborn Errors of Immunity to 5th-year medical students at Rīga Stradiņš University.**

Students take history from an AI parent, order investigations, submit differential diagnoses, and receive structured formative feedback — all in a realistic consultation format.

---

## What It Is

CaseRoom simulates the immunology outpatient consultation room. A clinical case opens with a brief description, a parent enters, and the student works through the case using four parallel tabs:

- 🗣 **History** — live conversation with the AI parent, who only reveals information when directly asked
- 🔬 **Investigations** — order any test in plain language; results appear from a clinician-authored case panel
- 📋 **Differentials** — submit and revise differential diagnoses; wrong paths trigger case-specific redirects
- ✅ **Final Answer** — structured submission covering diagnosis, management, genetic counselling, and explanation to the family

A contextual 💡 hint system tracks what the student has asked and ordered, and gives personalised guidance without revealing the diagnosis. The interface is available in English and Latvian.

## Cases

| ID | Patient | Diagnosis | Difficulty |
|----|---------|-----------|------------|
| XLA | Mārtins, 2yo boy | X-linked Agammaglobulinaemia | Intermediate |
| CGD | Emils, 3yo boy | Chronic Granulomatous Disease | Advanced |
| PFAPA | Leila, 3yo girl | PFAPA Syndrome | Intermediate |
| HIES | Klāra, 13yo girl | Hyper-IgE Syndrome (STAT3 LOF) | Advanced |
| THI | Toms, 10mo boy | Transient Hypogammaglobulinaemia of Infancy | Beginner |
| SCID | Rihards, 2.5mo boy | Artemis SCID + maternal T-cell engraftment + BCGitis | Advanced |

Each case includes a full parent script with gated information, investigation results with flagged abnormal values, case-specific wrong-path redirects, model management, and model genetic counselling used for feedback generation. New cases can be authored, versioned, and published by educators directly in the application.

## Architecture

CaseRoom is a two-service web application:

- **Backend** — FastAPI (Python 3.12), GraphQL via Strawberry at `/graphql`, a plain-HTTP SSE endpoint for streaming AI parent replies, async SQLAlchemy 2.0 + Alembic on PostgreSQL, Redis for sessions and rate limiting, and an ARQ worker for background jobs. Every student attempt is persisted as an append-only event log and replayed for review and research analytics.
- **Frontend** — React 18 + Vite + TypeScript, Apollo Client, CSS Modules, react-i18next (EN/LV).

The Anthropic API key lives **exclusively on the server** (`backend/app/llm/`). The browser never sees or sends any AI credentials.

Additional surfaces:

- **Educator dashboard** — cohorts, assignments, read-only transcript replay of assigned work, cohort analytics, and in-app case authoring with a draft/publish workflow.
- **Research MCP server** (`/mcp`, disabled by default) — a token-authenticated, read-only, pseudonymized and k-anonymized interface over the event log for research tooling. No free text and no direct identifiers are exposed.

## Security & Data Protection

- Passwordless magic-link authentication (6-digit student number, locked `@rsu.edu.lv` domain); opaque server-side sessions in an httpOnly cookie.
- Role-based access (student / staff / admin) enforced server-side on every query, mutation, nested field, and the SSE stream. Staff can read only attempts linked to assignments in cohorts they teach.
- PII (names, emails, login numbers) encrypted at rest with pgcrypto; lookups via peppered HMAC hashes.
- Rate limiting on registration, login-link requests, and link consumption.
- Research access is pseudonymized (HMAC with a dedicated pepper), k-anonymized, and withholds all free text.
- The application refuses to start in production if any required secret is missing.

Students are identifiable research subjects in the EU; hosting and data handling are subject to GDPR and the university's ethics-board approval.

## Development

Prerequisites: Docker + Docker Compose.

```bash
cp .env.example .env      # add a real ANTHROPIC_API_KEY
docker compose up --build
```

- Frontend: http://localhost:5173
- GraphQL + GraphiQL: http://localhost:8000/graphql
- Health: http://localhost:8000/health

Backend tests and lint:

```bash
cd backend
uv run --python 3.12 pytest          # unit suite
uv run --python 3.12 pytest -m dbintegration   # requires Postgres on :5433
uv run ruff check .
```

Frontend:

```bash
cd frontend
npm install
npm run lint && npm run typecheck && npm run test && npm run build
```

See `DEVELOPMENT.md` for the full guide and `CLAUDE.md` for contribution conventions.

## Deployment

Production runs as containers behind Caddy (automatic TLS): frontend (nginx), backend (uvicorn), ARQ worker, PostgreSQL, and Redis. See `deploy/docker-compose.prod.yml`, `deploy/Caddyfile`, and `deploy/.env.prod.example` — every value in the env example must be set; the backend fails fast on missing production secrets. Apply database migrations with `alembic upgrade head` before starting a new version.

## Project Structure

```
CaseRoom/
├── backend/            # FastAPI + GraphQL + SSE + workers
├── frontend/           # React + Vite + TypeScript
├── deploy/             # production compose, Caddyfile, env template
├── docs/               # architecture documentation (Antora)
├── .changeset/         # pending changelog entries (changesets)
├── IEI_Chatbot_v2.jsx  # original prototype — canonical source for ported logic
├── IEI_Chatbot_6.html  # compiled reference artifact of the prototype
└── docker-compose.yml  # development stack
```

## Documentation

Architectural design docs (component map, data-flow diagrams, security model, deployment,
research platform) live in `docs/` as an Antora site:

```bash
npm install
npm run docs:build      # renders to build/site
```

In production the built site is served at `https://caseroom.tech/docs/`, refreshed on every
deploy. When browsing this repository on GitHub, the AsciiDoc pages under
`docs/modules/ROOT/pages/` render directly, and the data-flow diagrams render in
[docs/data-flow.md](docs/data-flow.md).

Changelog entries are managed with [changesets](https://github.com/changesets/changesets):
every PR carries a `.changeset/*.md` file (CI enforces this), and the release workflow
aggregates them into `CHANGELOG.md` via a version PR.

`IEI_Chatbot_v2.jsx` is the historical single-file prototype this platform was ported from. It is kept as the reference for behavioural parity; it is not deployed and should not be run against a real API key from a browser.

## Clinical Context

This project was developed as part of a clinical genetics residency and PhD research project at Rīga Stradiņš University, Faculty of Medicine. Cases are grounded in the Latvian clinical context — including the first genetically confirmed SCID case in Latvia and the national TREC/KREC-based newborn screening programme launched in April 2023.

All clinical content — lab values, parent scripts, model diagnoses, management plans, and genetic counselling points — was authored and reviewed by a clinical genetics specialist. The AI does not determine what is clinically correct; it delivers and evaluates against content written by the clinician-educator.

## Author

**Marija Rozevska, MD** — clinical content and study design

---

*Created: March 2026*
