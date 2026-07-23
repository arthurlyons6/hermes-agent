# LIFECYCLE EVENT SCHEMA

Canonical stages:
- REQUEST_RECEIVED
- AUTH_VALIDATED
- ROUTE_SELECTED
- TOOLS_STARTED
- TOOLS_COMPLETED
- MODEL_REQUEST_STARTED
- MODEL_RESPONSE_RECEIVED
- MODEL_RESPONSE_VALIDATED
- RESPONSE_SERIALIZED
- TELEGRAM_SEND_STARTED
- TELEGRAM_SEND_SUCCEEDED
- TELEGRAM_SEND_FAILED
- REQUEST_COMPLETED
- REQUEST_FAILED

Required fields:
- timestamp
- request_id
- trace_id
- session_id
- component
- event
- status
- duration_ms where applicable
- provider where applicable
- model where applicable
- tool_count where applicable
- retry_count
- non-secret error_category where applicable

EOF