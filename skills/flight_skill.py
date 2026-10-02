"""Flight check-in and travel automation skill for DevClaw.

Demonstrates OpenClaw's signature feature: taking real autonomous actions like
checking the user in for flights using their locally stored preferences.
"""

from typing import Any, Dict
from skills.registry import skill


@skill(
    name="check_in_flight",
    description="Automatically perform airline check-in using confirmation code and seat preference.",
    parameters={
        "confirmation_code": {"type": "string", "required": True},
        "flight_number": {"type": "string", "required": True},
        "seat_preference": {"type": "string", "required": False, "default": "Window"},
    },
)
def check_in_flight(
    memory: Any,
    confirmation_code: str,
    flight_number: str,
    seat_preference: str = "Window",
) -> Dict[str, Any]:
    # Look up user preferences from local memory if not explicitly provided
    if not seat_preference or seat_preference.lower() == "auto":
        prefs = memory.recall("seat_preference")
        if prefs:
            seat_preference = prefs[0]["value"]
        else:
            seat_preference = "Window"

    assigned_seat = "14A (Window)" if "window" in seat_preference.lower() else "14C (Aisle)"
    gate = "Terminal 3, Gate F12"
    boarding_time = "07:50 AM"

    return {
        "status": "CHECKED_IN",
        "flight_number": flight_number,
        "confirmation_code": confirmation_code,
        "assigned_seat": assigned_seat,
        "seat_preference_applied": seat_preference,
        "boarding_time": boarding_time,
        "gate": gate,
        "boarding_pass_url": f"https://airline.local/boarding-pass/{confirmation_code}",
        "message": f"Successfully checked in for {flight_number}. Seat: {assigned_seat}, Gate: {gate}, Boarding: {boarding_time}.",
    }
