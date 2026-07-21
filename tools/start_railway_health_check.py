#!/usr/bin/env python3
"""Start Hermes and wait for its health endpoint before returning.


Use this as a Railway/process-supervisor start command, for example:
    python tools/start_railway_health_check.py

Observes:
- HERMES_GATEWAY_CMD: full argv list for the gateway process
- HERMES_HEALTH_URL: explicit /health URL
- HERMES_HEALTH_TIMEOUT: seconds to wait before giving up (default: 180)
"""

import json
import os
import shlex
import subprocess
import sys
import time
import urllib.parse
import urllib.request


def _health_url() -> str:
    explicit = os.environ.get("HERMES_HEALTH_URL", "").strip()
    if explicit:
        return explicit

    host = (
        os.environ.get("RAILWAY_PUBLIC_DOMAIN")
        or os.environ.get("RAILWAY_SERVICE_HERMES_Z0RV_URL")
        or os.environ.get("HERMES_PUBLIC_URL", "")
    )
    port = os.environ.get("PORT") or os.environ.get("HERMES_PORT") or "8080"
    path = os.environ.get("HERMES_HEALTH_PATH", "/health").strip() or "/health"

    if not host:
        host = f"127.0.0.1:{port}"
        return f"http://{host}{path}"

    if "://" not in host:
        host = f"http://{host}"
    if host.endswith("/"):
        host = host[:-1]
    return f"{host}{path}"


def _default_cmd() -> list[str]:
    return [
        sys.executable,
        "-m",
        "hermes_cli.main",
        "gateway",
        "run",
        "--no-supervise",
        "--railway-ready",
    ]


def _load_gateway_cmd() -> list[str]:
    raw = os.environ.get("HERMES_GATEWAY_CMD", "").strip()
    if raw:
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list) and parsed:
                return [str(x) for x in parsed]
        except Exception:
            pass
        return shlex.split(raw)
    return _default_cmd()


def main() -> int:
    cmd = _load_gateway_cmd()
    proc = subprocess.Popen(cmd)
    try:
        timeout = float(os.environ.get("HERMES_HEALTH_TIMEOUT", "180"))
        deadline = time.time() + timeout
        last = None
        health = _health_url()
        while time.time() < deadline:
            if proc.poll() is not None:
                break
            try:
                req = urllib.request.Request(health, method="GET")
                with urllib.request.urlopen(req, timeout=5) as resp:
                    if resp.status == 200:
                        sys.stdout.write(f"hermes health ready: {health}\n")
                        sys.stdout.flush()
                        return proc.wait()
            except Exception as exc:
                last = exc
            time.sleep(2)
        sys.stderr.write(f"hermes health probe failed: timeout / last_error={last} / url={health}\n")
        sys.stderr.flush()
        return proc.wait()
    finally:
        if proc.poll() is None:
            try:
                proc.terminate()
            except ProcessLookupError:
                pass
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
