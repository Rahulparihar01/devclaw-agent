"""Webhook Channel Adapter for DevClaw.

Demonstrates how external messaging webhooks (Telegram Bot API, WhatsApp Cloud API,
Discord webhooks) forward payloads directly into the local DevClaw Gateway.
"""

from typing import Any, Callable, Dict, Optional
from channels.base import BaseChannel
from core.models import ChannelMessage


class WebhookChannel(BaseChannel):
    """Simulates or connects an HTTP webhook receiver for chat applications."""

    def __init__(self, name: str, gateway_callback: Optional[Callable[[ChannelMessage], str]] = None):
        super().__init__(name=name)
        self.gateway_callback = gateway_callback
        self.outgoing_log = []

    def simulate_incoming_webhook(self, sender_id: str, text: str) -> str:
        """Simulates receiving an external HTTP webhook POST payload from WhatsApp or Telegram."""
        msg = ChannelMessage(
            channel=self.name,
            sender_id=sender_id,
            content=text,
        )
        if self.gateway_callback:
            return self.gateway_callback(msg)
        return "No gateway callback configured."

    def send(self, recipient_id: str, content: str):
        """Simulates sending an HTTP POST back to the messaging provider's API."""
        self.outgoing_log.append({"to": recipient_id, "text": content})
