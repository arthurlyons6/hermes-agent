import os, sys, traceback
sys.path.insert(0, '/app')
print("HERMES_HOME=", os.environ.get("HERMES_HOME"))
print("RAILWAY_ENVIRONMENT=", os.environ.get("RAILWAY_ENVIRONMENT"))
print("HERMES_ENV=", os.environ.get("HERMES_ENV"))
print("TELEGRAM_BOT_TOKEN=", bool(os.environ.get("TELEGRAM_BOT_TOKEN")))
try:
    os.chdir('/app')
    # Ensure project root is importable
    if '/app' not in sys.path:
        sys.path.insert(0, '/app')
    from gateway.config import GatewayConfig, _apply_env_overrides, Platform
    cfg = GatewayConfig()
    _apply_env_overrides(cfg)
    p = cfg.platforms.get(Platform.TELEGRAM)
    print("telegram_present=", p is not None)
    if p is not None:
        print("telegram_enabled=", p.enabled)
        print("telegram_token=", bool(getattr(p, 'token', '')))
        print("home_channel=", p.home_channel)
    print("health_url=", os.environ.get("HERMES_HEALTH_URL", ""))
except Exception:
    traceback.print_exc()
