# Railway Repair Plan

Generated: 2026-07-21T18:43:17.844380+00:00

## Actions
1. Add minimal `railway.toml` with `health.path = "/health"`.
2. Set `API_SERVER_HOST=0.0.0.0` in Railway env when needed for public health probes.
3. Ensure CMD keeps `hermes gateway run --no-supervise`.
4. Document `HERMES_HOME` volume mount path for Railway.
5. Add startup banner logging bind host/port and enabled platforms.
