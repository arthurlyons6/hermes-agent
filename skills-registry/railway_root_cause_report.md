# Railway Root Cause Report

Generated: 2026-07-21T18:43:17.844380+00:00

## Evidence Summary
- `GET /health` returns JSON without auth.
- `GET /health/detailed` requires Bearer auth.
- Default api_server host is `127.0.0.1`; port `8642`.
- Transient Telegram errors are swallowed by `gateway.run` exception handler.
- No `railway.toml` found in repo root.

## Gaps
1. Railway health probes from outside the container will fail if api_server binds `127.0.0.1`.
2. No in-repo Railway `railway.toml` health/restart policy.
3. Telegram startup failure behavior depends on adapter; needs explicit fail-soft gate.
