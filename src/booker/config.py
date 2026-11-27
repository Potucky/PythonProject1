"""Load suite settings from YAML, then apply environment overrides."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "settings.yaml"


@dataclass(frozen=True)
class Settings:
    """Runtime settings for the API client."""

    base_url: str
    timeout_seconds: float
    username: str
    password: str


def load_settings() -> Settings:
    """Read the YAML config and overlay BOOKER_* environment variables."""

    config_path = Path(os.environ.get("BOOKER_CONFIG", DEFAULT_CONFIG_PATH))
    if not config_path.is_file():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with config_path.open(encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}

    if not isinstance(raw, dict):
        raise ValueError(f"Config file must be a mapping: {config_path}")

    auth = raw.get("auth") or {}
    if not isinstance(auth, dict):
        raise ValueError("Config key 'auth' must be a mapping.")

    base_url = os.environ.get("BOOKER_BASE_URL", str(raw.get("base_url", ""))).strip()
    timeout_raw = os.environ.get("BOOKER_TIMEOUT", raw.get("timeout_seconds", 25))
    username = os.environ.get("BOOKER_USERNAME", str(auth.get("username", "")))
    password = os.environ.get("BOOKER_PASSWORD", str(auth.get("password", "")))

    if not base_url.startswith(("http://", "https://")):
        raise ValueError(f"base_url must start with http:// or https://, got {base_url!r}")

    try:
        timeout_seconds = float(timeout_raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"timeout_seconds must be a number, got {timeout_raw!r}") from exc
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be greater than zero.")

    return Settings(
        base_url=base_url.rstrip("/"),
        timeout_seconds=timeout_seconds,
        username=username,
        password=password,
    )
