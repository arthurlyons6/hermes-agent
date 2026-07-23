"""Centralized secrets interface for the Lyons Command Center."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class SecretDescriptor:
    name: str
    description: str
    required: bool = True


class SecretVault:
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
