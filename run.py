#!/usr/bin/env python3
"""DevClaw: A lightweight Python reference implementation of OpenClaw concepts.

Run options:
  python3 run.py               -> Interactive chat shell (CLI channel)
  python3 run.py --demo        -> Run automated end-to-end showcase scenarios
  python3 run.py --status      -> Inspect registered skills, local memory & database stats
"""

import argparse
import sys
from channels.cli_channel import CLIChannel
from core.gateway import DevClawGateway
from core.models import ChannelMessage
from demo_scenarios import run_all_scenarios
from skills.registry import registry


def print_status(gateway: DevClawGateway):
    print("\n🦞 DevClaw System Status & OpenClaw Architecture Inspection")
    print("=" * 60)
    skills = registry.list_skills()
    print(f"📦 Registered AgentSkills ({len(skills)} loaded):")
    for s in skills:
        print(f"   • {s.name:<22} - {s.description}")

    memories = gateway.memory.recall()
    print(f"\n🧠 Local Memories in SQLite ({len(memories)} entries):")
    for m in memories:
        print(f"   • [{m['category']}] {m['key']} = {m['value']}")

    events = gateway.memory.list_calendar_events()
    print(f"\n📅 Local Calendar Events ({len(events)} scheduled):")
    for ev in events:
        print(f"   • {ev['title']} at {ev['start_time']}")

    emails = gateway.memory.get_emails()
    print(f"\n📬 Local Inbox ({len(emails)} emails stored):")
    for em in emails:
        read_badge = "[READ]" if em["is_read"] else "[UNREAD]"
        print(f"   • {read_badge} From: {em['sender']} | {em['subject']}")

    logs = gateway.memory.get_recent_logs(limit=5)
    print(f"\n🛡️ Recent Audit Logs ({len(logs)} recorded):")
    for l in logs:
        print(f"   • {l['timestamp']} | {l['channel']} | {l['action_name']} ({l['status']})")
    print("=" * 60 + "\n")


def interactive_mode(gateway: DevClawGateway, engine_name: str = "Built-in Offline Engine"):
    cli = CLIChannel()
    gateway.register_channel(cli)
    cli.display_banner()
    print(f"\033[93m  • Active Engine: {engine_name}\033[0m\n")

    print("Type your message below (or type '/demo', '/status', or '/exit'):\n")

    while True:
        try:
            user_input = input("\033[96mYou (Chat) > \033[0m").strip()
            if not user_input:
                continue

            if user_input.lower() in ("/exit", "exit", "quit", "/quit"):
                print("\n🦞 Goodbye! DevClaw Gateway offline.\n")
                break

            if user_input.lower() == "/demo":
                run_all_scenarios()
                continue

            if user_input.lower() == "/status":
                print_status(gateway)
                continue

            if user_input.lower() == "/help":
                print("\n💡 Suggested prompts to test OpenClaw capabilities:")
                print("   1. 'What is OpenClaw and who created it?'")
                print("   2. 'What is the weather in Indore?'")
                print("   3. 'Find my flight in emails, check me in, and add it to calendar'")
                print("   4. 'Show me my unread emails'")
                print("   5. 'Send an email to alex@company.com saying see you at the sync'")
                print("   6. 'What events are on my calendar?'")
                print("   7. 'Remember that my seat preference is aisle and I prefer morning flights'")
                print("   8. 'What do you remember about my preferences?'")
                print("   9. 'Check local system health'")
                print("   10. '/status' to inspect the SQLite database")
                print("   11. '/demo' to run the automated tour")
                print("   12. '/real status' to query the real OpenClaw engine")
                print("   13. '/real skills' to list real OpenClaw bundled skills\n")
                continue

            # Real OpenClaw commands
            if user_input.lower().startswith("/real"):
                from openclaw_bridge import OpenClawBridge
                bridge = OpenClawBridge()
                sub = user_input[5:].strip().lower()
                if sub.startswith("skill "):
                    sname = sub.split()[1]
                    print(bridge.get_skill_info(sname))
                elif sub in ("skills", "skills list"):
                    print(bridge.list_skills())
                else:
                    print(bridge.status())
                continue

            # Send message to gateway
            msg = ChannelMessage(
                channel="cli",
                sender_id="local_user",
                content=user_input,
            )
            gateway.receive_message(msg)

        except (KeyboardInterrupt, EOFError):
            print("\n\n🦞 Goodbye! DevClaw Gateway stopped.\n")
            break


def main():
    parser = argparse.ArgumentParser(
        description="DevClaw: A clear, simple Python project demonstrating OpenClaw concepts."
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run the automated multi-step showcase scenarios",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Inspect registered skills and local SQLite memory",
    )
    parser.add_argument(
        "--real",
        action="store_true",
        help="Directly communicate with the real OpenClaw engine and skills",
    )
    parser.add_argument(
        "--ollama",
        action="store_true",
        help="Connect to local Ollama instance (100% offline local LLM)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="qwen2.5:1.5b",
        help="Model name when using Ollama (default: qwen2.5:1.5b)",
    )
    parser.add_argument(
        "--web",
        action="store_true",
        help="Launch the visual client-ready Web Dashboard on http://localhost:8000",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for Web Dashboard (default: 8000)",
    )
    args = parser.parse_args()

    if args.web:
        import web_app
        web_app.start_server(port=args.port, use_ollama=args.ollama, model=args.model)
        return

    if args.real:
        import use_real_openclaw
        use_real_openclaw.main()
        return

    engine_name = "Built-in Offline Engine"
    if args.ollama:
        from core.llm import OllamaLLM
        from core.agent import DevClawAgent
        llm = OllamaLLM(model=args.model)
        agent = DevClawAgent(llm=llm)
        gateway = DevClawGateway(agent=agent)
        engine_name = f"Ollama Local LLM ({args.model})"
    else:
        gateway = DevClawGateway()

    if args.demo:
        run_all_scenarios()
    elif args.status:
        print_status(gateway)
    else:
        interactive_mode(gateway, engine_name=engine_name)


if __name__ == "__main__":
    main()
