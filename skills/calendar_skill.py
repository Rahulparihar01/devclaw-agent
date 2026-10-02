"""Calendar skills for DevClaw (scheduling, agenda overview, conflict checking)."""

from typing import Any, Dict, List
from skills.registry import skill


@skill(
    name="list_calendar_events",
    description="List all upcoming events scheduled in the user's local calendar.",
    parameters={},
)
def list_calendar_events(memory: Any) -> List[Dict[str, Any]]:
    return memory.list_calendar_events()


@skill(
    name="add_calendar_event",
    description="Add a new event or meeting to the local calendar.",
    parameters={
        "title": {"type": "string", "required": True},
        "start_time": {"type": "string", "required": True, "description": "YYYY-MM-DD HH:MM:SS"},
        "end_time": {"type": "string", "required": True, "description": "YYYY-MM-DD HH:MM:SS"},
        "location": {"type": "string", "required": False, "default": "Virtual / TBD"},
        "description": {"type": "string", "required": False, "default": ""},
    },
)
def add_calendar_event(
    memory: Any,
    title: str,
    start_time: str,
    end_time: str,
    location: str = "Virtual / TBD",
    description: str = "",
) -> Dict[str, Any]:
    event_id = memory.add_calendar_event(
        title=title,
        start_time=start_time,
        end_time=end_time,
        location=location,
        description=description,
    )
    return {
        "status": "CREATED",
        "event_id": event_id,
        "title": title,
        "start_time": start_time,
        "end_time": end_time,
        "location": location,
        "message": f"Calendar event '{title}' scheduled for {start_time}.",
    }
