# Launch Stack Diagram

Approved architecture for launch stabilization and document production.

## Layers

```text
PostgreSQL
  ^
  | durable state, job persistence
  |
Hatchet worker
  ^
  | durable workflow execution, retries, schedules
  |
Hermes Workforce
  ^
  | drafting, assignment, review, redaction
  |
Promptfoo
  ^
  | automated quality and regression testing
  |
Quarto
  ^
  | institutional publishing and PDF rendering
  |
Docling
  ^
  | source document ingestion and fact/table extraction
  |
Source materials
```

## Runtime placement

- Hermes gateway runs on Railway as the primary runtime.
- ACP runs locally or as an opt-in plugin behind explicit activation.
- Hatchet runs as a bounded worker service with its own Postgres-backed state.
- Docling, Promptfoo, and Quarto run on a separate Railway document worker.
- All cross-service boundaries are governed by ACP audit, approval, and metering.
