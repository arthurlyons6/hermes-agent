"""centralized secrets interface for the Lyons Command Center.

preferred backends, in order:
1. OS-native credential store
2. herm

design supports future expansion without changing callers.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class SecretDescriptor:
    name: str
    description: str
    required: bool = True
    backend: str = "environment"


class SecretVault:
    """read-only facade for secrets retrieval."""

    def get(self, name: str, default: Optional[str] = None) -> Optional[str]:
        value = os.environ.get(name, default)
        if value is None:
            if default is None:
                raise KeyError(f"missing required secret: {name}")
            return default
        return value


VAULT = SecretVault()


def require(name: str, description: str = "") -> str:
    value = VAULT.get(name)
    if value is None:
        raise KeyError(f"missing required secret: {name} — {description}")
    return value


def optional(name: str, default: str = "") -> str:
    return VAULT.get(name, default) or default
