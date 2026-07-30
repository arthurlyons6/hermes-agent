# Design System — Lyons Command Center

**Technical Architecture Standards**

---

## Table of Contents

1. [Core Principles](#core-principles)
2. [Architecture Patterns](#architecture-patterns)
3. [Code Organization](#code-organization)
4. [Tool Development](#tool-development)
5. [Skill Development](#skill-development)
6. [Plugin Architecture](#plugin-architecture)
7. [MCP Integration](#mcp-integration)
8. [Data Flow Patterns](#data-flow-patterns)
9. [Performance Standards](#performance-standards)
10. [Testing Standards](#testing-standards)

---

## Core Principles

1. **Per-conversation prompt caching is sacred.** A long-lived conversation reuses a cached prefix every turn. Anything that mutates past context, swaps toolsets, or rebuilds the system prompt mid-conversation invalidates that cache.

2. **The core is a narrow waist; capability lives at the edges.** Every model tool added is sent on every API call, so the bar for a new core tool is high.

3. **Preserve the invariant: every line traces to the request.** No dead code, no placeholder implementations.

---

## Architecture Patterns

### Pattern 1: CLI Command + Skill
For subscriptions, scheduled tasks, service setup:
- CLI command (`hermes <subcommand>`)
- Guided by a skill
- Zero model-tool footprint

### Pattern 2: Service-gated Tool
For structured params/returns that only appear when prerequisite is configured:
- `check_fn` for availability
- Zero footprint otherwise

### Pattern 3: Plugin
For third-party/niche/user-specific capability:
- Lives in `~/.hermes/plugins/`
- Discovered at runtime
- No core modifications needed

---

## Code Organization

### Hermes Core
```
hermes-agent/
├── run_agent.py          # Core conversation loop
├── model_tools.py        # Tool orchestration
├── cli.py                # CLI orchestrator
└── hermes_state.py       # Session store
```

### Tools
```
tools/
├── registry.py           # Tool registration
└── *.py                  # Tool implementations
```

### Gateway
```
gateway/
├── run.py                # Gateway runner
└── platforms/            # Platform adapters
```

---

## Tool Development

### Built-in Tool Example
```python
from tools.registry import registry

def check_requirements() -> bool:
    return bool(os.getenv("EXAMPLE_API_KEY"))

def example_tool(param: str, task_id: str = None) -> str:
    return json.dumps({"success": True, "data": "..."})

registry.register(
    name="example_tool",
    toolset="example",
    schema={...},
    handler=lambda args, **kw: example_tool(...),
    check_fn=check_requirements,
)
```

### Toolset Definition
Tools must be added to `toolsets.py`:
- `_HERMES_CORE_TOOLS` for all platforms
- Or a new toolset

---

## Skill Development

### Skill Structure
```
skills/<name>/
├── SKILL.md              # Frontmatter + documentation
├── scripts/              # Supporting scripts
├── references/           # Reference docs
└── templates/            # Templates
```

### SKILL.md Frontmatter
```yaml
---
name: Skill Name
description: One-line description
category: Domain
author: Your Name
version: 1.0.0
---
```

---

## Plugin Architecture

### Memory Provider Plugin
```
plugins/memory/<name>/
├── __init__.py           # Plugin entry point
├── cli.py                # Optional CLI commands
└── provider.py           # MemoryProvider implementation
```

### Plugin Lifecycle
- `pre_tool_call`, `post_tool_call`
- `pre_llm_call`, `post_llm_call`
- `on_session_start`, `on_session_end`
- `register_tool()` for new tools

---

## MCP Integration

### MCP Server Pattern
```yaml
# config.yaml
mcp:
  servers:
    - name: github
      command: python -m mcp_servers.github
      args: ["--api-key", "${GITHUB_API_KEY}"]
```

### MCP Tool Discovery
- Auto-discovered via MCP client
- Zero permanent core-schema footprint
- Reusable by any MCP host

---

## Data Flow Patterns

### Session Store
```
hermes_state.py → SessionDB (SQLite with FTS5)
```

### Memory Flow
```
Agent turn → MemoryProvider.sync_turn() → Store
Query → MemoryProvider.prefetch() → Results
```

### Compression Pipeline
```
Conversation → Curator → Summary → Replace history
```

---

## Performance Standards

### Response Time Goals
- **CLI Chat:** < 2s for simple queries
- **Gateway Message:** < 5s end-to-end
- **Tool Execution:** < 30s (configurable)
- **Memory Sync:** < 1s per turn

### Resource Limits
- **Context Window:** Respect model limits
- **Token Budget:** Configurable per-task
- **Rate Limits:** Auto-throttled with backoff

---

## Testing Standards

### Test Types
1. **Unit Tests:** Individual function behavior
2. **Integration Tests:** Tool resolution chains
3. **E2E Tests:** Full conversation flows
4. **Regression Tests:** 86+ passing minimum

### Test File Structure
```
tests/
├── agent/
├── cli/
├── tools/
├── gateway/
└── skills/
```

### Quality Gate: 86+ Passing Tests
All tests must pass in clean environment:
```bash
scripts/run_tests.sh
```

---

## Security Patterns

### Secrets Management
- `.env` for API keys only
- `config.yaml` for all other settings
- No hardcoded credentials

### Network Security
- TLS 1.3 for all communications
- Proper certificate validation
- No self-signed certificates in production

---

## Documentation Standards

### Code Comments
- Explain "why", not "what"
- Document complex algorithms
- Link to external resources

### User Documentation
- Executive summaries first
- Technical details in expandable sections
- Step-by-step instructions

---

## Version Control

### Commit Structure
```
<type>(<scope>): <subject>

<body>

<footer>
```

Types: feat, fix, docs, style, refactor, perf, test, chore

### Branch Naming
- `feature/<name>` for new features
- `fix/<issue>` for bug fixes
- `docs/<topic>` for documentation

---

## Review Checklist

Before submitting a PR:

- [ ] All tests pass (86+)
- [ ] No generic UI patterns
- [ ] Meets quality gate scores
- [ ] Security review complete
- [ ] Documentation updated
- [ ] No credentials in code
- [ ] Follows architecture patterns
- [ ] Executive summary included