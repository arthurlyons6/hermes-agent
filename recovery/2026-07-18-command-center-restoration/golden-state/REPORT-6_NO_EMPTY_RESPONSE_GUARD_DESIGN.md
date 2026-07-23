# REPORT 6 — No-Empty-Response Guard Design
Status: Proposed design only. No production change.

## Trigger
- tool execution completed
- no final assistant response produced
- observed locally as absence of `Turn ended` or equivalent terminal response event, subject to future correlation_id confirmation

## Step 1 — Detect
- Detect when tool sequence closes without `Turn ended` / terminal response lifecycle event within configured timeout after last tool completion.

## Step 2 — Record
Record only non-sensitive metadata:
- request_id
- timestamp
- provider
- model
- tool names
- retry count
- context estimate
- error_class

## Step 3 — Retry once
- Reuse existing tool results
- Send controlled retry instruction:
  "Tool execution completed successfully, but no final response was produced. Using the existing tool results, provide the final user-facing answer now. Do not rerun tools."
- Do not rerun side-effecting tools automatically.

## Step 4 — Approved fallback once
- If retry fails, use the approved fallback once if configured.
- Pass only necessary context and tool summaries.
- Record fallback usage and provider/model pair.

## Step 5 — Controlled failure message
- If retry and fallback fail, return:
  "Your request was processed, but the model did not produce a usable final response. The failure was recorded under Incident [ID]. No side-effecting action was repeated. Please retry the request."
- Include request_id or incident reference.

## Side-effect protection
- Retry never reruns side-effecting tools.
- Reuse only read-only/terminal tool outputs.
- External actions: no duplicates.

## Events to emit
- final_response_empty detected
- final_response_retry sent
- fallback_model_used
- response recovery: success / failure

## Validation requirements before deployment
- Unit test normal flow: no retry
- Unit test empty response: one retry
- Unit test double empty: fallback then structured incident message
- Unit test side-effecting tool: tool not rerun
- Integration test with correlation_id propagation

