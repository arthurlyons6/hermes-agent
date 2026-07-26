# AUDIT FINDING: Railway container `railway run` uses LOCAL Hermes venv, not container runtime

gateway.run imports successfully but shows no output for `_start_early_api_server`. The module imports cleanly. The fix IS present in the Railway container's source tree. The question is: does Hermes CLI call gateway.run.start_gateway() on startup?

I need to check the Hermes CLI entry point to understand how the gateway runner is invoked.