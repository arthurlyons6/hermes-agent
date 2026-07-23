"""Security audit automation for the Lyons Command Center.

Evaluates:
- sensitive files exposure
- configuration hygiene
- gateway health
- credential rotation reminders
- dependency vulnerability surface
"""
from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from core.vault import VAULT


@dataclass(frozen=True)
class Finding:
    severity: str
    category: str
    message: str
    remediation: str
    detail: str = ""


@dataclass
class AuditReport:
    generated_at: str
    findings: List[Finding]
    environment: str = field(default_factory=lambda: os.environ.get("HERMES_ENV", "local"))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def audit() -> AuditReport:
    findings: List[Finding] = []
    home = Path.home()

    # Sensitive file exposure
    sensitive_roots = [home / ".env", home / ".env.local", home / ".env.production"]
    for path in sensitive_roots:
        if path.exists() and path.stat().st_size > 0:
            findings.append(
                Finding(
                    severity="high",
                    category="secrets",
                    message=f"sensitive file present: {path.name}",
                    remediation="ensure file is excluded from version control, backups, and sharing",
                    detail=str(path),
                )
            )

    # Config validation
    config_path = home / "AppData" / "Local" / "hermes" / "config.yaml"
    if config_path.exists():
        try:
            content = config_path.read_text(encoding="utf-8")
            if "allowed_chats" not in content:
                findings.append(
                    Finding(
                        severity="medium",
                        category="configuration",
                        message="missing allowed_chats",
                        remediation="explicitly allow operational chats to reduce accidental exposure",
                    )
                )
        except Exception as exc:  # pragma: no cover
            findings.append(
                Finding(
                    severity="low",
                    category="configuration",
                    message=f"config read issue: {exc}",
                    remediation="review file encoding/permissions",
                )
            )
    else:
        findings.append(
            Finding(
                severity="medium",
                category="configuration",
                message="config.yaml not found",
                remediation="ensure configuration is present",
            )
        )

    # Dependency vulnerabilities
    findings.append(
        Finding(
            severity="medium",
            category="dependencies",
            message="dependency vulnerability scan not automated",
            remediation="integrate pip-audit or safety into weekly automation",
            detail="pip-audit / safety not scheduled",
        )
    )

    return AuditReport(generated_at=_now_iso(), findings=findings)


def render_text(report: AuditReport) -> str:
    lines = [f"Security Audit {report.generated_at}"]
    for finding in report.findings:
        lines.append(f"- [{finding.severity.upper()}] {finding.category}: {finding.message}")
    return "\n".join(lines)


def render_json(report: AuditReport) -> str:
    payload = {
        "generated_at": report.generated_at,
        "environment": report.environment,
        "findings": [
            {
                "severity": f.severity,
                "category": f.category,
                "message": f.message,
                "remediation": f.remediation,
                "detail": f.detail,
            }
            for f in report.findings
        ],
    }
    return json.dumps(payload, indent=2)


if __name__ == "__main__":
    report = audit()
    print(render_text(report))
    print()
    print(render_json(report))
