"""Small Restful Booker client. Steps call this instead of requests directly."""

from __future__ import annotations

from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class BookerClient:
    """Session wrapper for the public booking API.

    Update, partial update, and delete send the demo token as a cookie,
    which is what this API expects. Calls made with ``authenticated=False``
    send no cookie, even if the client already holds a token.
    """

    def __init__(self, base_url: str, timeout_seconds: float, retries: int = 2) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.token: str | None = None
        self.created_ids: list[int] = []
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})
        retry = Retry(
            total=retries,
            connect=retries,
            read=retries,
            status=retries,
            backoff_factor=0.4,
            status_forcelist=(502, 503, 504),
            allowed_methods=frozenset(["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD"]),
            raise_on_status=False,
            respect_retry_after_header=True,
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def close(self) -> None:
        self.session.close()

    def ping(self) -> requests.Response:
        return self._send("GET", "/ping")

    def authenticate(self, username: str, password: str) -> requests.Response:
        response = self._send(
            "POST",
            "/auth",
            json_body={"username": username, "password": password},
        )
        self.token = _token_from(response)
        return response

    def create_booking(self, payload: dict[str, Any]) -> requests.Response:
        response = self._send("POST", "/booking", json_body=payload)
        booking_id = _booking_id_from(response)
        if booking_id is not None:
            self.created_ids.append(booking_id)
        return response

    def get_booking(self, booking_id: int) -> requests.Response:
        return self._send("GET", f"/booking/{booking_id}")

    def update_booking(
        self,
        booking_id: int,
        payload: dict[str, Any],
        *,
        authenticated: bool = True,
    ) -> requests.Response:
        return self._send(
            "PUT",
            f"/booking/{booking_id}",
            json_body=payload,
            authenticated=authenticated,
        )

    def partial_update_booking(
        self,
        booking_id: int,
        payload: dict[str, Any],
        *,
        authenticated: bool = True,
    ) -> requests.Response:
        return self._send(
            "PATCH",
            f"/booking/{booking_id}",
            json_body=payload,
            authenticated=authenticated,
        )

    def delete_booking(self, booking_id: int, *, authenticated: bool = True) -> requests.Response:
        return self._send("DELETE", f"/booking/{booking_id}", authenticated=authenticated)

    def _send(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
        authenticated: bool = False,
    ) -> requests.Response:
        # Ignore cookies the session may have stored. Auth is an explicit header.
        self.session.cookies.clear()
        headers: dict[str, str] = {}
        if authenticated:
            if not self.token:
                raise RuntimeError("This call needs an auth token. Authenticate first.")
            headers["Cookie"] = f"token={self.token}"
        return self.session.request(
            method,
            f"{self.base_url}{path}",
            json=json_body,
            headers=headers,
            timeout=self.timeout_seconds,
        )


def _json_object(response: requests.Response) -> dict[str, Any] | None:
    content_type = response.headers.get("Content-Type", "")
    if "json" not in content_type.lower():
        return None
    try:
        body = response.json()
    except ValueError:
        return None
    if isinstance(body, dict):
        return body
    return None


def _token_from(response: requests.Response) -> str | None:
    body = _json_object(response)
    if body is None:
        return None
    token = body.get("token")
    if isinstance(token, str) and token:
        return token
    return None


def _booking_id_from(response: requests.Response) -> int | None:
    body = _json_object(response)
    if body is None:
        return None
    booking_id = body.get("bookingid")
    if isinstance(booking_id, int):
        return booking_id
    return None
