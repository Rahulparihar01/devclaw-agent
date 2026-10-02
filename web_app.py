"""Web Dashboard Server for DevClaw (Client Demonstration).

Built with Python Standard Library (zero external dependencies).
Serves:
- Single-page client dashboard at http://localhost:8000
- REST APIs for live chat, real-time SQLite state, and OpenClaw inspection
"""

import argparse
import json
import os
import sys
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Any, Dict

from core.gateway import DevClawGateway
from core.models import ChannelMessage
from openclaw_bridge import OpenClawBridge


class DevClawWebHandler(BaseHTTPRequestHandler):
    """Handles HTTP requests for the DevClaw Web UI and REST API."""

    gateway: DevClawGateway = None
    engine_name: str = "Built-in Offline Engine"
    claw_bridge: OpenClawBridge = None

    def _set_headers(self, status: int = 200, content_type: str = "application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(200)

    def do_GET(self):
        url_path = self.path.split("?")[0]

        if url_path in ("/", "/index.html"):
            html_file = Path(__file__).resolve().parent / "web" / "index.html"
            if html_file.exists():
                with open(html_file, "rb") as f:
                    content = f.read()
                self._set_headers(200, "text/html; charset=utf-8")
                self.wfile.write(content)
            else:
                self._set_headers(404, "text/plain")
                self.wfile.write(b"web/index.html not found.")
            return

        if url_path == "/api/state":
            mem = self.gateway.memory
            state = {
                "emails": mem.get_emails(),
                "calendar": mem.list_calendar_events(),
                "memories": mem.recall(),
                "audit_logs": mem.get_recent_logs(limit=25),
                "engine": self.engine_name,
                "openclaw": {
                    "version": self.claw_bridge.version(),
                    "skills_snippet": self.claw_bridge.list_skills()[:800] + "...",
                },
            }
            self._set_headers(200, "application/json")
            self.wfile.write(json.dumps(state).encode("utf-8"))
            return

        self._set_headers(404, "text/plain")
        self.wfile.write(b"Not Found")

    def do_POST(self):
        url_path = self.path.split("?")[0]

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        try:
            payload = json.loads(body)
        except Exception:
            payload = {}

        if url_path == "/api/chat":
            user_msg = payload.get("message", "").strip()
            channel = payload.get("channel", "whatsapp")
            if not user_msg:
                self._set_headers(400, "application/json")
                self.wfile.write(json.dumps({"error": "Empty message"}).encode("utf-8"))
                return

            msg = ChannelMessage(
                channel=channel,
                sender_id="client_demo_user",
                content=user_msg,
            )
            reply = self.gateway.receive_message(msg)
            now = datetime.now().strftime("%H:%M")

            self._set_headers(200, "application/json")
            self.wfile.write(json.dumps({"reply": reply, "timestamp": now}).encode("utf-8"))
            return

        if url_path == "/api/demo":
            # Run the automated flight check-in and inbox triage scenario
            msg = ChannelMessage(
                channel="whatsapp",
                sender_id="+15550192834",
                content="Hey DevClaw, find my flight to SFO in my emails, check me in using my preferences, and put it on my calendar.",
            )
            reply = self.gateway.receive_message(msg)
            self._set_headers(200, "application/json")
            self.wfile.write(json.dumps({"reply": reply}).encode("utf-8"))
            return

        if url_path in ("/api/chat/new", "/api/chat/clear", "/api/chat/reset"):
            self.gateway.reset_conversation()
            self._set_headers(200, "application/json")
            self.wfile.write(json.dumps({"status": "SUCCESS", "message": "Fresh chat session started. Database records preserved."}).encode("utf-8"))
            return

        if url_path == "/api/reset":
            self.gateway.memory.reset_data()
            self._set_headers(200, "application/json")
            self.wfile.write(json.dumps({"status": "SUCCESS", "message": "Demo data reset to clean initial state."}).encode("utf-8"))
            return

        self._set_headers(404, "text/plain")
        self.wfile.write(b"Not Found")

    def do_HEAD(self):
        self.do_GET()

    def log_message(self, format, *args):
        # Concise logging using standard format % args
        try:
            sys.stderr.write(f"[WebUI] {self.address_string()} - {format % args}\n")
        except Exception:
            pass


def start_server(port: int = 8000, use_ollama: bool = False, model: str = "qwen2.5:1.5b"):
    engine_name = "Built-in Offline Engine"
    if use_ollama:
        from core.llm import OllamaLLM
        from core.agent import DevClawAgent
        llm = OllamaLLM(model=model)
        agent = DevClawAgent(llm=llm)
        gateway = DevClawGateway(agent=agent)
        engine_name = f"Ollama Local LLM ({model})"
    else:
        gateway = DevClawGateway()

    DevClawWebHandler.gateway = gateway
    DevClawWebHandler.engine_name = engine_name
    DevClawWebHandler.claw_bridge = OpenClawBridge()

    HTTPServer.allow_reuse_address = True

    # Try binding requested port, fallback to next available if busy
    httpd = None
    active_port = port
    for p in range(port, port + 20):
        try:
            httpd = HTTPServer(("", p), DevClawWebHandler)
            active_port = p
            break
        except OSError:
            continue

    if not httpd:
        print(f"\n❌ Could not bind to any port between {port} and {port + 20}.\n")
        return

    print("\n" + "=" * 65)
    print(f"🦞 DevClaw Web Dashboard running at:")
    print(f"   👉 http://localhost:{active_port}/")
    print(f"   👉 http://127.0.0.1:{active_port}/")
    print(f"• Active Engine: {engine_name}")
    print(f"• Press Ctrl+C to stop.")
    print("=" * 65 + "\n")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🦞 Web Dashboard stopped.\n")
        httpd.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DevClaw Client Web Dashboard")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000)")
    parser.add_argument("--ollama", action="store_true", help="Use local Ollama model")
    parser.add_argument("--model", type=str, default="qwen2.5:1.5b", help="Model name for Ollama")
    args = parser.parse_args()

    start_server(port=args.port, use_ollama=args.ollama, model=args.model)
