## Railway Deployment Audit — Final Report

### Repository
- **Repo**: arthurlyons6/hermes-agent
- **Branch**: master
- **HEAD**: 99e44f6 (build: add pyproject.toml and Dockerfile for Railway repo-based builds)
- **Remote HEAD**: 99e44f6 (synced)

### Changes Committed
1. **c4961f6** — gateway/run.py + gateway/api_server.py with early API server startup
2. **2aa3882/99e44f6** — Dockerfile + pyproject.toml for Railway repo-based builds

### Railway Build Path Audit
- **Before audit**: LyonsCommandCenter had NO Dockerfile, NO pyproject.toml
- **Railway was using**: A pre-baked Docker image with Hermes 0.19.0 pre-installed from PyPI at `/opt/hermes/.venv/`
- **Pushing source commits alone did NOT trigger a Docker rebuild** — Railway was serving the static pre-baked image
- **The old crash-loop gateway/run.py** (API server inside slow platform loop) was baked into the pre-baked image

### Root Cause of Crash Loop Confirmed
Railway sends SIGTERM before Hermes API server binds to 0.0.0.0:3006 and serves GET /health. The crash loop occurred because:
1. Platform initialization (Telegram adapter, MCP discovery, etc.) runs first  
2. API server only binds after all initialization completes
3. Railway's startup probe fires SIGTERM before step 2 finishes
4. Container crashes and restarts in a loop

### Fixes Applied
- **c4961f6**: gateway/run.py starts APIServerAdapter and binds GET /health to 0.0.0.0:3006 BEFORE platform initialization starts
- **99e44f6**: Dockerfile tells Railway to build from repo source (`pip install .`) so the startup-order fix is included; pyproject.toml enables `pip install .` to work

### Dockerfile Build Status
- Railway Dockerfile build FAILED (Deploy failed 5m) — reason not visible from CLI
- Pre-baked image is still serving the OLD crash loop
- Railway CLI does not surface Docker build failure logs
- **Build failure reason requires Railway Dashboard access**

### What Has Been Proven
- ✅ Source code fix committed and pushed (c4961f6)
- ✅ Dockerfile + pyproject.toml committed and pushed (99e44f6)
- ✅ Provider layer (6136bc9) preserved, unchanged
- ✅ 79 tests pass, 0 failures
- ✅ OpenRouter /api/v1/model/{model} → HTTP 200 (live)
- ✅ Nous GET /v1/models?model= → HTTP 200 (live)
- ❌ Railway deploy not yet verified (Dockerfile build failed silently)

### Next Action Required
The Dockerfile build failed but the failure reason is only visible in the Railway Dashboard build logs. The user needs to:
1. Open Railway Dashboard → hermes-z0Rv → Build logs
2. Identify the Docker build failure
3. Fix the build
4. Re-trigger deploy from 99e44f6
5. Verify /health returns HTTP 200