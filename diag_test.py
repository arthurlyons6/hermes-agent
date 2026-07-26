import asyncio
import os
import sys

# Simulate what happens in the container
print("HERMES_DIAG_START", flush=True)

# Step 1: Check env vars
print(f"PORT={os.environ.get('PORT')}", flush=True)
print(f"API_SERVER_PORT={os.environ.get('API_SERVER_PORT')}", flush=True)
print(f"HERMES_ENV={os.environ.get('HERMES_ENV')}", flush=True)

# Step 2: Try importing gateway
try:
    import gateway.run as gr
    print(f"gateway.run imported OK", flush=True)
    print(f"_start_early_api_server is coroutine: {asyncio.iscoroutinefunction(gr._start_early_api_server)}", flush=True)
except Exception as e:
    print(f"IMPORT ERROR: {e}", flush=True)
    sys.exit(1)

# Step 3: Try importing APIServerAdapter
try:
    from gateway.api_server import APIServerAdapter
    print(f"APIServerAdapter imported OK", flush=True)
    print(f"start is coroutine: {asyncio.iscoroutinefunction(APIServerAdapter.start)}", flush=True)
except Exception as e:
    print(f"APIServerAdapter IMPORT ERROR: {e}", flush=True)
    sys.exit(1)

# Step 4: Try actually starting the server
async def test_server():
    port = int(os.environ.get("API_SERVER_PORT") or os.environ.get("PORT") or "3006")
    print(f"HERMES_DIAG trying to start server on port {port}", flush=True)
    
    cfg = type('Cfg', (), {'value': 'api_server', 'extra': type('Extra', (), {'port': port, 'host': '0.0.0.0'})()})()
    cfg.port = port
    cfg.host = '0.0.0.0'
    
    adapter = APIServerAdapter(cfg)
    print(f"HERMES_DIAG adapter created: {type(adapter)}", flush=True)
    
    try:
        await adapter.start()
        print(f"HERMES_DIAG API server started OK on port {port}", flush=True)
    except Exception as e:
        print(f"HERMES_DIAG API server FAILED: {type(e).__name__}: {e}", flush=True)
        import traceback
        traceback.print_exc()

asyncio.run(test_server())
print("HERMES_DIAG_END", flush=True)
