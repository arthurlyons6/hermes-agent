# REPORT 5 — Correlation ID Architecture
Status: Proposed design only. No production change.

## Requirement
Assign one immutable Request ID at request entry and flow it through every observable stage.

## Stages with required ID inclusion
- Telegram inbound update
- Gateway accepted request
- Authentication decision
- Agent router dispatch
- Tool execution start/complete
- Model provider request start/complete
- Tool-result serialization
- Response generation
- Telegram send start/complete
- Error/incident record

## ID format
Use high-entropy short ID, e.g., 32-character hex, generated at gateway entry and logged with every subsequent event for the request.

## Log format requirement
Each log entry includes:
- timestamp
- request_id
- stage
- component
- duration_since_stage_start
- status
- error_class
- provider/model
- tool_count
Non-sensitive context only; no tokens or secrets.

## Storage
- Pass request_id in request context/metadata map only; do not persist full inbound payloads.
- Short-lived for active request; archived summary records only.

## Compatibility
- Compatible with existing logging structure; additive field only.
- No encrypted/sealed payload required.

