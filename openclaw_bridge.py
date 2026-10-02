"""Python Bridge for the Real OpenClaw Engine.

This module provides a direct Python interface to control, query, and orchestrate
the real OpenClaw CLI and Gateway daemon installed on your machine.

Features:
- Check OpenClaw Gateway and daemon status
- Query real OpenClaw skills (bundled & ClawHub)
- Search and inspect OpenClaw skills
- Dispatch agent turns and messaging through OpenClaw
- Run health checks and doctor diagnostics
"""

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional


class OpenClawError(Exception):
    """Raised when an OpenClaw CLI or Gateway operation fails."""
    pass


class OpenClawBridge:
    """Python client and controller for the real OpenClaw engine."""

    def __init__(self, profile: str = "dev", binary_path: Optional[str] = None):
        self.profile = profile
        self.binary_path = binary_path or self._discover_binary()

    def _discover_binary(self) -> str:
        """Locates the OpenClaw executable (local node_modules or system PATH)."""
        local_node_bin = Path(__file__).resolve().parent / "node_modules" / ".bin" / "openclaw"
        if local_node_bin.exists():
            return str(local_node_bin)

        which_claw = shutil.which("openclaw")
        if which_claw:
            return which_claw

        # Fallback to npx
        return "npx -y openclaw"

    def _run_cmd(self, args: List[str], timeout: int = 30) -> subprocess.CompletedProcess:
        """Executes an OpenClaw CLI command with the configured profile."""
        cmd = self.binary_path.split() + ["--profile", self.profile] + args
        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return res
        except subprocess.TimeoutExpired:
            raise OpenClawError(f"OpenClaw command timed out: {' '.join(cmd)}")
        except Exception as e:
            raise OpenClawError(f"Failed to execute OpenClaw: {str(e)}")

    def version(self) -> str:
        """Returns the installed OpenClaw version."""
        res = self._run_cmd(["--version"])
        if res.returncode == 0:
            return res.stdout.strip()
        return "Unknown"

    def status(self, deep: bool = False) -> str:
        """Returns the real OpenClaw system, gateway, and channel status."""
        args = ["status"]
        if deep:
            args.append("--deep")
        res = self._run_cmd(args)
        return res.stdout if res.stdout else res.stderr

    def list_skills(self) -> str:
        """Returns the catalog of real OpenClaw bundled & installed AgentSkills."""
        res = self._run_cmd(["skills", "list"])
        return res.stdout if res.stdout else res.stderr

    def search_skills(self, query: str) -> str:
        """Searches ClawHub for available OpenClaw community skills."""
        res = self._run_cmd(["skills", "search", query])
        return res.stdout if res.stdout else res.stderr

    def get_skill_info(self, skill_name: str) -> str:
        """Fetches detailed documentation and parameter requirements for an OpenClaw skill."""
        res = self._run_cmd(["skills", "info", skill_name])
        return res.stdout if res.stdout else res.stderr

    def run_agent(self, message: str, deliver: bool = False) -> str:
        """Runs an autonomous agent turn through OpenClaw with the given message."""
        args = ["agent", "--message", message]
        if deliver:
            args.append("--deliver")
        res = self._run_cmd(args)
        return res.stdout if res.stdout else res.stderr

    def doctor(self) -> str:
        """Runs the OpenClaw diagnostic tool to inspect health and configuration."""
        res = self._run_cmd(["doctor"])
        return res.stdout if res.stdout else res.stderr

    def gateway_probe(self) -> str:
        """Probes the OpenClaw Gateway daemon to check connectivity and reachability."""
        res = self._run_cmd(["gateway", "probe"])
        return res.stdout if res.stdout else res.stderr


# Global default instance
claw = OpenClawBridge()
