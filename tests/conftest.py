"""Fixtures shared by the API scenarios."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
import requests

from booker.client import BookerClient
from booker.config import Settings, load_settings
from steps.booking_steps import ScenarioState


@pytest.fixture(scope="session")
def settings() -> Settings:
    return load_settings()


@pytest.fixture(scope="session")
def require_booking_service(settings: Settings) -> None:
    """Fail the API scenarios once when the public demo API is unreachable."""

    client = BookerClient(settings.base_url, settings.timeout_seconds)
    try:
        try:
            response = client.ping()
        except requests.RequestException as exc:
            pytest.exit(
                f"Restful Booker is not reachable at {settings.base_url}: {exc}",
                returncode=2,
            )
        if response.status_code != 201:
            pytest.exit(
                f"Restful Booker ping returned HTTP {response.status_code}, expected 201.",
                returncode=2,
            )
    finally:
        client.close()


@pytest.fixture
def state() -> ScenarioState:
    return ScenarioState()


@pytest.fixture
def client(settings: Settings, require_booking_service: None) -> Iterator[BookerClient]:
    """One client per scenario. Bookings it created are deleted afterwards."""

    api = BookerClient(settings.base_url, settings.timeout_seconds)
    try:
        yield api
    finally:
        _delete_created(api, settings)
        api.close()


def _delete_created(api: BookerClient, settings: Settings) -> None:
    if not api.created_ids:
        return
    try:
        if not api.token:
            api.authenticate(settings.username, settings.password)
        if not api.token:
            return
        for booking_id in list(api.created_ids):
            try:
                api.delete_booking(booking_id)
            except (requests.RequestException, RuntimeError):
                continue
    except (requests.RequestException, RuntimeError):
        return
