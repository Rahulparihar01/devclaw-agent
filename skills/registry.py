"""Skill Registry and decorator for OpenClaw-style AgentSkills.

Skills are pluggable modules that provide the agent with executable capabilities.
Each skill exposes:
- name: Unique identifier for the tool
- description: Explains what the tool does (used by the LLM)
- parameters: Argument schema description
- execute(): The python callable that runs the tool
"""

import inspect
from typing import Any, Callable, Dict, List, Optional
from core.models import ToolResult


class Skill:
    """Represents an executable skill in DevClaw."""

    def __init__(
        self,
        name: str,
        description: str,
        func: Callable,
        parameters: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.description = description
        self.func = func
        self.parameters = parameters or self._inspect_parameters(func)

    def _inspect_parameters(self, func: Callable) -> Dict[str, Any]:
        """Automatically infers parameter documentation from function signature."""
        sig = inspect.signature(func)
        params = {}
        for param_name, param in sig.parameters.items():
            if param_name in ("context", "memory"):
                continue  # Injected dependencies
            annotation = (
                param.annotation.__name__
                if param.annotation != inspect.Parameter.empty
                else "string"
            )
            default = (
                param.default
                if param.default != inspect.Parameter.empty
                else "REQUIRED"
            )
            params[param_name] = {
                "type": annotation,
                "required": default == "REQUIRED",
                "default": None if default == "REQUIRED" else default,
            }
        return params

    def run(self, context: Any, **kwargs) -> ToolResult:
        """Executes the skill and wraps the result safely."""
        try:
            # Check if function expects context/memory
            sig = inspect.signature(self.func)
            call_kwargs = dict(kwargs)
            if "context" in sig.parameters:
                call_kwargs["context"] = context
            if "memory" in sig.parameters:
                call_kwargs["memory"] = context.memory

            result = self.func(**call_kwargs)
            return ToolResult(
                skill_name=self.name,
                success=True,
                output=result,
            )
        except Exception as e:
            return ToolResult(
                skill_name=self.name,
                success=False,
                output=None,
                error=f"Error in {self.name}: {str(e)}",
            )


class SkillRegistry:
    """Central registry of all available agent skills."""

    def __init__(self):
        self._skills: Dict[str, Skill] = {}

    def register(self, skill: Skill):
        self._skills[skill.name] = skill

    def get(self, name: str) -> Optional[Skill]:
        return self._skills.get(name)

    def list_skills(self) -> List[Skill]:
        return list(self._skills.values())

    def get_schemas(self) -> List[Dict[str, Any]]:
        """Returns JSON-compatible schemas of all skills for the LLM."""
        schemas = []
        for s in self._skills.values():
            schemas.append({
                "name": s.name,
                "description": s.description,
                "parameters": s.parameters,
            })
        return schemas


# Global registry instance
registry = SkillRegistry()


def skill(name: str, description: str, parameters: Optional[Dict[str, Any]] = None):
    """Decorator to register a function as an OpenClaw AgentSkill."""
    def decorator(func: Callable):
        sk = Skill(name=name, description=description, func=func, parameters=parameters)
        registry.register(sk)
        return func
    return decorator
