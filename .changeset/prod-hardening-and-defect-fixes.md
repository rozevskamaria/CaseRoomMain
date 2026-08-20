---
"caseroom": minor
---

Production hardening and defect fixes ahead of university infrastructure review.

Defect fixes:

- Attempt projection cache (phase/status/completed_at) now syncs on every event commit, so the educator dashboard shows real attempt states.
- `attempt` query returns stored timestamps and status; dashboard attempt rows carry the case slug.
- Cases authored in-app can be assigned to cohorts and served by `case(id:)` — the static registry gate was removed.
- Research `get_feedback` filters by attempt in SQL instead of loading every feedback row.
- Event log is read once per mutation (incremental fold); `submitFinalAnswer` batches its field-set events; the events DataLoader batches per-attempt loads in one query.

Security hardening:

- The backend refuses to start in production with missing secrets (`ANTHROPIC_API_KEY`, `PGCRYPTO_KEY`, `LOGIN_HASH_PEPPER`, `RESEND_API_KEY`), a localhost `PUBLIC_BASE_URL`, or MCP enabled without its token and pepper.
- Unexpected GraphQL resolver errors are masked; expected application errors pass through.
- `devLogin` is disabled everywhere except `APP_ENV=development`.
- Magic-link consumption is rate limited per IP.
- Production uvicorn trusts proxy headers so per-IP rate limits see real client addresses behind Caddy.
- Caddy sends HSTS, nosniff, frame-deny, referrer and permissions policies.
- `deploy/.env.prod.example` lists every required production value; the README no longer documents browser-side API keys.
