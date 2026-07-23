# TEST PLAN

Coverage:
- Normal no-tool response
- Normal tool-assisted response
- Multiple tools
- Empty final response
- Provider timeout
- Provider empty completion
- Serialization failure
- Telegram send failure
- Telegram timeout
- Budget exhaustion
- Context pressure
- Side-effecting tool completed before model failure
- Retry without tool replay
- Fallback success
- Fallback failure
- Secret-redaction validation
- Correlation ID continuity

Requirements:
- Unit tests before integration tests
- Behavioral guard tests only after instrumentation is validated
- Side-effect protection tests mandatory
- Rollback tests for each phase

EOF