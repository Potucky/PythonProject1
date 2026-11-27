"""Step definitions. Each step calls BookerClient; none open HTTP on their own."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests
from pytest_bdd import given, parsers, then, when

from booker.client import BookerClient
from booker.config import Settings
from booker.payloads import new_booking

_EMPTY = "(none)"


@dataclass
class ScenarioState:
    """Response and booking remembered between steps in one scenario."""

    response: requests.Response | None = None
    booking_id: int | None = None
    payload: dict[str, Any] | None = None


def _blank(value: str) -> str:
    return "" if value == _EMPTY else value


def _response(state: ScenarioState) -> requests.Response:
    if state.response is None:
        raise AssertionError("No response was recorded. A When step should run first.")
    return state.response


def _body_snippet(response: requests.Response) -> str:
    text = response.text[:300].replace("\n", " ")
    if "token" in text.lower():
        return '{"token":"***"}'
    return text


def _assert_status(response: requests.Response, expected: int) -> None:
    if response.status_code != expected:
        raise AssertionError(
            f"Expected HTTP {expected}, got {response.status_code}. Body: {_body_snippet(response)}"
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


def _require_json(response: requests.Response) -> dict[str, Any]:
    body = _json_object(response)
    if body is None:
        raise AssertionError(
            f"Expected a JSON object, got HTTP {response.status_code}: {_body_snippet(response)}"
        )
    return body


def _booking_record(response: requests.Response) -> dict[str, Any]:
    body = _require_json(response)
    nested = body.get("booking")
    if isinstance(nested, dict):
        return nested
    return body


def _require_booking(state: ScenarioState) -> int:
    if state.booking_id is None:
        raise AssertionError("This step needs a booking id from an earlier step.")
    return state.booking_id


def _remember_created(state: ScenarioState, response: requests.Response, payload: dict[str, Any]) -> None:
    state.response = response
    state.payload = payload
    body = _json_object(response)
    if body is None:
        return
    booking_id = body.get("bookingid")
    if isinstance(booking_id, int):
        state.booking_id = booking_id


def _assert_fields(response: requests.Response, expected: dict[str, Any]) -> None:
    record = _booking_record(response)
    for field_name, expected_value in expected.items():
        actual = record.get(field_name)
        if actual != expected_value:
            raise AssertionError(
                f'Expected {field_name} "{expected_value}", got "{actual}". '
                f"Body: {_body_snippet(response)}"
            )


@given("the booking service is healthy")
def booking_service_is_healthy(client: BookerClient, state: ScenarioState) -> None:
    state.response = client.ping()
    _assert_status(state.response, 201)


@given("I am authenticated with the demo account")
def authenticated_with_demo_account(
    client: BookerClient,
    settings: Settings,
    state: ScenarioState,
) -> None:
    state.response = client.authenticate(settings.username, settings.password)
    _assert_status(state.response, 200)
    if not client.token:
        raise AssertionError("Demo authentication did not return a token.")


@given(parsers.parse('a booking exists for "{firstname}" "{lastname}"'))
def booking_exists(
    client: BookerClient,
    state: ScenarioState,
    firstname: str,
    lastname: str,
) -> None:
    payload = new_booking(firstname, lastname)
    response = client.create_booking(payload)
    _assert_status(response, 200)
    _remember_created(state, response, payload)
    if state.booking_id is None:
        raise AssertionError(f"Create did not return a booking id. Body: {_body_snippet(response)}")


@when(parsers.parse('I create a booking for "{firstname}" "{lastname}" priced at {totalprice:d}'))
def create_priced_booking(
    client: BookerClient,
    state: ScenarioState,
    firstname: str,
    lastname: str,
    totalprice: int,
) -> None:
    payload = new_booking(firstname, lastname, totalprice)
    _remember_created(state, client.create_booking(payload), payload)


@when(parsers.parse('I create a booking with only "{field}" set to "{value}"'))
def create_incomplete_booking(
    client: BookerClient,
    state: ScenarioState,
    field: str,
    value: str,
) -> None:
    state.payload = {field: value}
    state.booking_id = None
    state.response = client.create_booking(state.payload)


@when(parsers.parse('I authenticate as "{username}" with password "{password}"'))
def authenticate_as(
    client: BookerClient,
    state: ScenarioState,
    username: str,
    password: str,
) -> None:
    state.response = client.authenticate(_blank(username), _blank(password))


@when("I read that booking")
def read_that_booking(client: BookerClient, state: ScenarioState) -> None:
    state.response = client.get_booking(_require_booking(state))


@when(parsers.parse("I read booking {booking_id:d}"))
def read_booking_by_id(client: BookerClient, state: ScenarioState, booking_id: int) -> None:
    state.booking_id = booking_id
    state.response = client.get_booking(booking_id)


@when(parsers.parse('I replace that booking with first name "{firstname}"'))
def replace_booking(client: BookerClient, state: ScenarioState, firstname: str) -> None:
    booking_id = _require_booking(state)
    if state.payload is None:
        raise AssertionError("This step needs the payload from the booking that was created.")
    payload = {**state.payload, "firstname": firstname}
    state.payload = payload
    state.response = client.update_booking(booking_id, payload)


@when(parsers.parse('I partially update that booking last name to "{lastname}"'))
def patch_last_name(client: BookerClient, state: ScenarioState, lastname: str) -> None:
    booking_id = _require_booking(state)
    state.response = client.partial_update_booking(booking_id, {"lastname": lastname})
    if state.payload is not None:
        state.payload = {**state.payload, "lastname": lastname}


@when("I delete that booking")
def delete_booking(client: BookerClient, state: ScenarioState) -> None:
    state.response = client.delete_booking(_require_booking(state))


@when(parsers.parse("I {action} that booking without a token"))
def change_booking_without_token(client: BookerClient, state: ScenarioState, action: str) -> None:
    booking_id = _require_booking(state)
    if client.token is not None:
        raise AssertionError("This scenario must call the API with no token stored.")
    if action == "replace":
        if state.payload is None:
            raise AssertionError("Replace needs the original booking payload.")
        state.response = client.update_booking(booking_id, state.payload, authenticated=False)
    elif action == "partially update":
        state.response = client.partial_update_booking(
            booking_id,
            {"lastname": "Nope"},
            authenticated=False,
        )
    elif action == "delete":
        state.response = client.delete_booking(booking_id, authenticated=False)
    else:
        raise AssertionError(f"Unknown action {action!r}. Expected replace, partially update, or delete.")


@then(parsers.parse("the response status is {status:d}"))
def response_status_is(state: ScenarioState, status: int) -> None:
    _assert_status(_response(state), status)


@then("the response includes a booking id")
def response_includes_booking_id(state: ScenarioState) -> None:
    booking_id = _require_json(_response(state)).get("bookingid")
    if not isinstance(booking_id, int):
        raise AssertionError("Response JSON did not include an integer bookingid.")
    state.booking_id = booking_id


@then("the response does not include a booking id")
def response_omits_booking_id(state: ScenarioState) -> None:
    body = _json_object(_response(state))
    if body is not None and "bookingid" in body:
        raise AssertionError("Incomplete payload was stored and returned a booking id.")


@then("the response contains an auth token")
def response_contains_token(client: BookerClient, state: ScenarioState) -> None:
    token = _require_json(_response(state)).get("token")
    if not isinstance(token, str) or not token:
        raise AssertionError("Response JSON did not include an auth token.")
    if client.token != token:
        raise AssertionError("The client did not keep the token from the auth response.")


@then("the response explains that the credentials are bad")
def response_explains_bad_credentials(state: ScenarioState) -> None:
    body = _require_json(_response(state))
    if "token" in body:
        raise AssertionError("Invalid credentials returned a token.")
    reason = body.get("reason")
    if reason != "Bad credentials":
        raise AssertionError(f'Expected reason "Bad credentials", got {reason!r}.')


@then(parsers.parse('the booking name is "{firstname}" "{lastname}"'))
def booking_name_is(state: ScenarioState, firstname: str, lastname: str) -> None:
    _assert_fields(_response(state), {"firstname": firstname, "lastname": lastname})


@then(parsers.parse("the booking total price is {totalprice:d}"))
def booking_total_price_is(state: ScenarioState, totalprice: int) -> None:
    _assert_fields(_response(state), {"totalprice": totalprice})
