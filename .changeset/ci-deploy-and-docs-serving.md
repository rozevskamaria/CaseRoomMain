---
"caseroom": patch
---

CI now builds the Antora documentation site and, on green default-branch builds, deploys to production over SSH (repo + docs sync, image rebuild, migrations, seed, container recreation, health smoke-check). The architecture docs are served at `/docs/` by Caddy.
