#!/usr/bin/env python3
"""Railway start wrapper for Hermes.

Starts a minimal /health server on Railway's $PORT so Railway considers the
deployment healthy, then launches the real gateway. Keeps the gateway process
in the foreground so Railway can supervise it normally.

Env:
- PORT / HERMES_PORT: port to bind /health on (Railway sets PORT automatically)
- HERMES_LISTEN_HOST: bind host for /health, defaults to 0.0.0.0 on Railway.
- HERMES_GATEWAY_CMD: JSON or shell argv for the gateway process.
- HERMES_HEALTH_PATH: path served, defaults to "/health".
"""

import json
import os
import shlex
import socket
import subprocess
import sys
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.request import Request, urlopen
from urllib.error import URLError


class _HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
            try:
                expected = os.environ.get("HERMES_HEALTH_PATH", "/health").strip() or "/health"
                if self.path != expected:
                    self.send_response(404)
                    self.end_headers()
                    return
                body = b'{"status":"ok","service":"hermes-agent","source":"start_railway_health_check"}'
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except Exception:
                try:
                    self.send_response(500)
                    self.end_headers()
                except Exception:
                    pass


def _is_railway() -> bool:
    env = (os.environ.get("RAILWAY_ENVIRONMENT") or os.environ.get("HERMES_ENV") or "").strip().lower()
    return env == "railway"


def _listen_host(default: str = "0.0.0.0") -> str:
    return (os.environ.get("HERMES_LISTEN_HOST") or default).strip() or default


def _listen_port(default: str = "8080") -> int:
    raw = (
        os.environ.get("PORT")
        or os.environ.get("HERMES_PORT")
        or default
    )
    try:
        return int(str(raw).strip())
    except (TypeError, ValueError):
        return int(default)


def _health_path(default: str = "/health") -> str:
    raw = os.environ.get("HERMES_HEALTH_PATH", default).strip()
    return raw if raw else default


def _sidecar_url(host: str, port: int) -> str:
    return f"http://{host}:{port}{_health_path()}"


def _start_sidecar(host: str, port: int) -> HTTPServer:
    server = HTTPServer((host, port), _HealthHandler)
    server.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return server


def _probe_ready(url: str, timeout: float = 5.0) -> bool:
    try:
        with urlopen(Request(url, method="GET"), timeout=timeout) as resp:
            return resp.status == 200
    except Exception:
        return False


def _default_cmd() -> list[str]:
    return [
        sys.executable,
        "-m",
        "hermes_cli.main",
        "gateway",
        "run",
        "--no-supervise",
    ]


def _load_gateway_cmd() -> list[str]:
    raw = os.environ.get("HERMES_GATEWAY_CMD", "").strip()
    if not raw:
        return _default_cmd()
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list) and parsed:
            return [str(x) for x in parsed]
    except Exception:
        pass
    return shlex.split(raw)


def main() -> int:
    host = _listen_host("0.0.0.0" if _is_railway() else "127.0.0.1")
    port = _listen_port()
    expected_path = _health_path()
    url = _sidecar_url("127.0.0.1", port)

    sidecar = _start_sidecar(host, port)
    cmd = _load_gateway_cmd()
    proc = subprocess.Popen(cmd)

    try:
        timeout = float(os.environ.get("HERMES_HEALTH_TIMEOUT", "180"))
        deadline = time.time() + timeout
        last = None
        ready = False
        while time.time() < deadline:
            if proc.poll() is not None:
                break
            if _probe_ready(url):
                print(f"hermes-health-ready url={url} path={expected_path} port={port}", flush=True)
                ready = True
                break
            try:
                last = urlopen(Request(url, method="GET"), timeout=2).read()
            except Exception as exc:
                last = exc
            time.sleep(2)
        if not ready:
            print(f"hermes-health-failed url={url} last={last}", flush=True, file=sys.stderr)
            code = proc.wait()
            return code
        return proc.wait()
    finally:
        try:
            sidecar.shutdown()
        except Exception:
            pass
        if proc.poll() is None:
            try:
                proc.terminate()
            except ProcessLookupError:
                pass
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
