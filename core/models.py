"""Core data models representing messages, actions, and execution context in DevClaw.

These match OpenClaw's architectural abstractions:
- Channels send incoming Messages to the Gateway.
- The Agent decomposes intent into ToolCalls (Skills).
- ToolCalls return ToolResults that update local memory and inform the agent's response.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class ChannelMessage:
    """Represents an incoming or outgoing message from any connected messaging channel
    (e.g., WhatsApp, Telegram, Discord, CLI).
    """
    channel: str              # e.g., "whatsapp", "telegram", "cli"
    sender_id: str            # e.g., "+1234567890", "@vinayak", "local_user"
    content: str              # Message body
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolCall:
    """Represents an autonomous action the agent chooses to invoke."""
    skill_name: str
    arguments: Dict[str, Any]
    thought: Optional[str] = None


@dataclass
class ToolResult:
    """Represents the outcome of an executed skill."""
    skill_name: str
    success: bool
    output: Any
    error: Optional[str] = None


@dataclass
class AgentTurn:
    """A single execution turn of the agent's reasoning loop."""
    thought: str
    tool_calls: List[ToolCall] = field(default_factory=list)
    tool_results: List[ToolResult] = field(default_factory=list)
    final_reply: Optional[str] = None
