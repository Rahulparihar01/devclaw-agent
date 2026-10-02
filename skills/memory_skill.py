"""Local Memory and preference skills for DevClaw."""

from typing import Any, Dict, List, Optional
from skills.registry import skill


@skill(
    name="remember_fact",
    description="Save a personal fact, preference, or context item into persistent local memory.",
    parameters={
        "category": {"type": "string", "required": True, "description": "e.g., preference, contact, travel, work"},
        "key": {"type": "string", "required": True, "description": "Short identifier (e.g. seat_preference)"},
        "value": {"type": "string", "required": True, "description": "The information to remember"},
    },
)
def remember_fact(memory: Any, category: str, key: str, value: str) -> Dict[str, Any]:
    memory.remember(category=category, key=key, value=value)
    return {
        "status": "STORED",
        "category": category,
        "key": key,
        "value": value,
        "message": f"Saved to local memory: [{category}] {key} = {value}",
    }


@skill(
    name="recall_facts",
    description="Recall stored preferences, contacts, or personal facts from local memory.",
    parameters={
        "query": {"type": "string", "required": False, "default": "", "description": "Keyword to search for"},
    },
)
def recall_facts(memory: Any, query: str = "") -> List[Dict[str, Any]]:
    memories = memory.recall(query=query if query else None)
    return [
        {
            "category": m["category"],
            "key": m["key"],
            "value": m["value"],
            "last_updated": m["updated_at"],
        }
        for m in memories
    ]
