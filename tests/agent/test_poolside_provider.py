"""Poolside provider integration checks."""

from __future__ import annotations

import os

from providers import get_provider_profile, list_providers


def test_poolside_profile_loaded():
    profile = get_provider_profile("poolside")
    assert profile is not None
    assert profile.name == "poolside"
    assert profile.base_url == "https://inference.poolside.ai/v1"
    assert profile.fallback_models == ("poolside/laguna-m.1",)
    assert profile.env_vars == ("POOLSIDE_API_KEY",)
    assert profile.api_mode == "chat_completions"


def test_poolside_in_list_providers():
    names = sorted(getattr(p, "name", None) for p in list_providers() if getattr(p, "name", None) == "poolside")
    assert names == ["poolside"]
