"""Booking bodies shared by the step definitions."""

from __future__ import annotations

from typing import Any

DEFAULT_TOTAL_PRICE = 150
CHECK_IN = "2026-12-01"
CHECK_OUT = "2026-12-05"


def new_booking(
    firstname: str,
    lastname: str,
    totalprice: int = DEFAULT_TOTAL_PRICE,
) -> dict[str, Any]:
    """Return a complete booking payload the demo API will store."""

    return {
        "firstname": firstname,
        "lastname": lastname,
        "totalprice": totalprice,
        "depositpaid": True,
        "bookingdates": {
            "checkin": CHECK_IN,
            "checkout": CHECK_OUT,
        },
        "additionalneeds": "Breakfast",
    }
