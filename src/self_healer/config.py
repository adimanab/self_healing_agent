"""
self_healer.config
==================
Centralised configuration — all settings are read from environment variables.

Users set these env vars before running pytest:
    API_KEY        — Required. Your LLM API key.
    LLM_MODEL      — Required. LLM model name.
    BASE_URL       — Optional. Defaults to OpenAI's API endpoint.
    TEMPERATURE    — Optional. LLM temperature (0.0-1.0). Defaults to 0.4.
"""

import os


def _get_required(name: str) -> str:
    """Return an env var or raise a helpful error."""
    val = os.getenv(name)
    if not val:
        raise RuntimeError(
            f"[self-healer] Environment variable '{name}' is not set. "
            f"Please export it before running your tests."
        )
    return val


def get_api_key() -> str:
    return _get_required("API_KEY")


def get_model_name() -> str:
    return _get_required("LLM_MODEL")


def get_base_url() -> str:
    return os.getenv("BASE_URL", "")


def get_temperature() -> float:
    return float(os.getenv("TEMPERATURE", 0.4))
