"""Settings load from YAML and can be overridden without a code change."""

from __future__ import annotations

from pathlib import Path

import pytest

from booker.config import load_settings


def test_default_settings_point_at_the_public_demo(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "BOOKER_CONFIG",
        "BOOKER_BASE_URL",
        "BOOKER_TIMEOUT",
        "BOOKER_USERNAME",
        "BOOKER_PASSWORD",
    ):
        monkeypatch.delenv(name, raising=False)

    settings = load_settings()

    assert settings.base_url == "https://restful-booker.herokuapp.com"
    assert settings.username == "admin"
    assert settings.password == "password123"
    assert settings.timeout_seconds == 30


def test_environment_overrides_yaml(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / "settings.yaml"
    config_path.write_text(
        "\n".join(
            [
                "base_url: https://example.test",
                "timeout_seconds: 5",
                "auth:",
                "  username: from-file",
                "  password: from-file",
                "",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("BOOKER_CONFIG", str(config_path))
    monkeypatch.setenv("BOOKER_BASE_URL", "https://override.test")
    monkeypatch.setenv("BOOKER_TIMEOUT", "12")
    monkeypatch.setenv("BOOKER_USERNAME", "from-env")
    monkeypatch.delenv("BOOKER_PASSWORD", raising=False)

    settings = load_settings()

    assert settings.base_url == "https://override.test"
    assert settings.timeout_seconds == 12
    assert settings.username == "from-env"
    assert settings.password == "from-file"


def test_rejects_a_base_url_without_a_scheme(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / "settings.yaml"
    config_path.write_text(
        "\n".join(
            [
                "base_url: restful-booker.herokuapp.com",
                "timeout_seconds: 5",
                "auth:",
                "  username: admin",
                "  password: password123",
                "",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("BOOKER_CONFIG", str(config_path))
    monkeypatch.delenv("BOOKER_BASE_URL", raising=False)

    with pytest.raises(ValueError, match="base_url"):
        load_settings()
