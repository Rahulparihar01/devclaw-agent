"""Interactive Terminal Channel Simulator for DevClaw.

Emulates receiving and sending messages through messaging apps like WhatsApp or Telegram,
complete with stylish terminal formatting.
"""

from datetime import datetime
from channels.base import BaseChannel


class CLIChannel(BaseChannel):
    """Terminal chat interface supporting colored chat bubbles and action badges."""

    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    MAGENTA = "\033[95m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"

    def __init__(self, name: str = "cli"):
        super().__init__(name=name)

    def display_banner(self):
        """Displays the DevClaw welcome banner."""
        banner = f"""{self.CYAN}{self.BOLD}
  ╔══════════════════════════════════════════════════════════╗
  ║    🦞 DevClaw — Local Autonomous Agent for Python       ║
  ║    Inspired by OpenClaw · Privacy-First · Action-Driven  ║
  ╚══════════════════════════════════════════════════════════╝{self.RESET}
{self.DIM}  • Channel: Interactive Chat Shell (Simulating WhatsApp / Telegram)
  • Gateway: localhost (local-first, runs on your machine)
  • Storage: SQLite (devclaw.db)
  • Type /help for suggested commands or /exit to quit.{self.RESET}
"""
        print(banner)

    def send(self, recipient_id: str, content: str):
        """Renders the outgoing reply from DevClaw."""
        now = datetime.now().strftime("%H:%M:%S")
        print(f"\n{self.GREEN}{self.BOLD}🦞 DevClaw {self.DIM}({now}){self.RESET}")
        for line in content.split("\n"):
            print(f"  {line}")
        print()
