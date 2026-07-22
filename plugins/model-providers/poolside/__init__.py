"""Poolside provider profile.

Poolside is exposed here as an OpenAI-compatible provider for Hermes.
Model discovery remains fallback-only until the live catalog shape is
confirmed against ``https://api.poolside.ai/v1/models``.
"""

from __future__ import annotations

from providers import register_provider
from providers.base import ProviderProfile

poolside = ProviderProfile(
    name="poolside",
    display_name="Poolside",
    description="Poolside OpenAI-compatible model API",
    env_vars=("POOLSIDE_API_KEY",),
    base_url="https://inference.poolside.ai/v1",
    auth_type="api_key",
    aliases=("poolside-ai",),
    fallback_models=("poolside/laguna-m.1",),
    default_aux_model="poolside/laguna-m.1",
    supports_vision=True,
    supports_vision_tool_messages=True,
    default_headers={
        "X-Provider-Role": "engineering-primary",
        "X-Lyons-Workflow": "code+debug+refactor+arch-review",
    },
)

register_provider(poolside)
