"""System inspection skills for DevClaw (Runs on your machine)."""

import os
import platform
from typing import Any, Dict
from skills.registry import skill


@skill(
    name="get_system_status",
    description="Check the status and hardware info of the local host machine running the agent.",
    parameters={},
)
def get_system_status(memory: Any) -> Dict[str, Any]:
    return {
        "status": "ONLINE",
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "python_version": platform.python_version(),
        "working_directory": os.getcwd(),
        "message": "DevClaw Gateway daemon running locally and healthy.",
    }
