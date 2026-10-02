"""Skills package for DevClaw. Automatically loads all registered skills."""

from skills.registry import registry, skill
import skills.email_skill
import skills.calendar_skill
import skills.flight_skill
import skills.memory_skill
import skills.system_skill
import skills.weather_skill

__all__ = ["registry", "skill"]
