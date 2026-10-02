"""Base Channel Adapter."""

from abc import ABC, abstractmethod


class BaseChannel(ABC):
    """Abstract interface for messaging platform integrations."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def send(self, recipient_id: str, content: str):
        """Sends an outgoing message through this channel."""
        pass
