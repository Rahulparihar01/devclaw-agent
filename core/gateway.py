"""Central Gateway for DevClaw (matching OpenClaw's local gateway architecture).

The Gateway daemon runs locally on the user's computer. It:
1. Connects to one or more channel adapters (WhatsApp, Telegram, CLI).
2. Forwards incoming messages to the DevClawAgent.
3. Routes the agent's action responses back to the originating channel.
4. Maintains audit transparency and local state.
"""

from typing import Dict, List, Optional
from core.agent import DevClawAgent
from core.memory import LocalMemory
from core.models import ChannelMessage


class ChannelAdapter:
    """Base class for messaging channel adapters."""
    name: str = "base"

    def send(self, recipient_id: str, content: str):
        raise NotImplementedError


class DevClawGateway:
    """Central daemon orchestrating channels, memory, and agent execution."""

    def __init__(
        self,
        memory: Optional[LocalMemory] = None,
        agent: Optional[DevClawAgent] = None,
    ):
        self.memory = memory or LocalMemory()
        self.agent = agent or DevClawAgent(memory=self.memory)
        self.channels: Dict[str, ChannelAdapter] = {}

    def register_channel(self, channel: ChannelAdapter):
        """Registers a chat channel adapter (e.g. Telegram, WhatsApp, CLI)."""
        self.channels[channel.name] = channel

    def receive_message(self, message: ChannelMessage) -> str:
        """Entrypoint for all incoming messages from any connected platform."""
        reply = self.agent.handle_message(message)

        # Dispatch back through the channel adapter if registered
        adapter = self.channels.get(message.channel)
        if adapter:
            adapter.send(message.sender_id, reply)

        return reply

    def reset_conversation(self):
        """Clears conversational memory for a fresh chat session without touching database data."""
        self.agent.conversation_history = []
