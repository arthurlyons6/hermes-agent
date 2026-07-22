# ACP Local Metering Plan

## Scope

Local Hermes metering and optional cloud governance for tool calls and API spend.

## Acceptance criteria

- ACP installs in a temp Hermes venv without core runtime mutations.
- Hook registration succeeds.
- Local metering path writes valid records.
- Network timeout or SQLite lock fails open.
- `acp-hermes report` output is present.

## Steps

1. Install the ACP plugin in a controlled temp HERMES_HOME.
2. Verify local metering SQLite path and record schema.
3. Confirm no coupling to existing HERMES_HOME files.
4. Confirm cloud login is explicit and manual, not automatic.
5. Document opt-in config in README if absent.

## Rollback

- Disable ACP plugin.
- Remove `~/.acp` credentials.
- Revert plugin install only.
