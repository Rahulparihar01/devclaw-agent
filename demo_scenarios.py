"""Preset demonstration scenarios highlighting OpenClaw's signature capabilities.

These run through end-to-end autonomous workflows:
1. Multi-Step Travel Assistant (Email lookup -> Flight Check-in -> Calendar booking)
2. Inbox Triage & Reply (Reading unread emails -> Drafting responses)
3. Local Memory & Personalization (Zero cloud leakage, SQLite storage)
4. Local Audit & Action Transparency (Audit logs of executed actions)
"""

import time
from core.gateway import DevClawGateway
from core.models import ChannelMessage


def run_scenario_flight(gateway: DevClawGateway):
    print("\n" + "=" * 65)
    print("🚀 SCENARIO 1: Autonomous Flight Check-in & Calendar Sync")
    print("   OpenClaw's iconic showcase: Taking real actions on your behalf.")
    print("=" * 65)

    msg = ChannelMessage(
        channel="whatsapp",
        sender_id="+15550192834",
        content="Hey DevClaw, find my flight to SFO in my emails, check me in using my preferences, and put it on my calendar.",
    )
    print(f"\n📱 [Incoming via WhatsApp from {msg.sender_id}]:")
    print(f"   \"{msg.content}\"")
    time.sleep(0.5)

    reply = gateway.receive_message(msg)
    print(f"\n🦞 [DevClaw WhatsApp Reply]:\n{reply}")


def run_scenario_inbox(gateway: DevClawGateway):
    print("\n" + "=" * 65)
    print("📬 SCENARIO 2: Inbox Triage & Automated Reply")
    print("   Organizes your inbox and handles correspondence autonomously.")
    print("=" * 65)

    msg1 = ChannelMessage(
        channel="telegram",
        sender_id="@vinayak",
        content="Show me my unread emails.",
    )
    print(f"\n📱 [Incoming via Telegram from {msg1.sender_id}]:")
    print(f"   \"{msg1.content}\"")
    time.sleep(0.5)
    reply1 = gateway.receive_message(msg1)
    print(f"\n🦞 [DevClaw Telegram Reply]:\n{reply1}")

    msg2 = ChannelMessage(
        channel="telegram",
        sender_id="@vinayak",
        content="Send an email to alex@company.com saying Friday at 3 PM works great.",
    )
    print(f"\n📱 [Incoming via Telegram from {msg2.sender_id}]:")
    print(f"   \"{msg2.content}\"")
    time.sleep(0.5)
    reply2 = gateway.receive_message(msg2)
    print(f"\n🦞 [DevClaw Telegram Reply]:\n{reply2}")


def run_scenario_memory(gateway: DevClawGateway):
    print("\n" + "=" * 65)
    print("🧠 SCENARIO 3: Local Persistent Memory & Zero-Cloud Privacy")
    print("   Stores user preferences locally in SQLite. Never sent to third parties.")
    print("=" * 65)

    msg1 = ChannelMessage(
        channel="cli",
        sender_id="vinayak",
        content="Remember that my favorite airline is United and I always need gluten-free meals.",
    )
    print(f"\n💬 [User CLI Input]:\n   \"{msg1.content}\"")
    time.sleep(0.5)
    reply1 = gateway.receive_message(msg1)
    print(f"\n🦞 [DevClaw Reply]:\n{reply1}")

    msg2 = ChannelMessage(
        channel="cli",
        sender_id="vinayak",
        content="What do you remember about my preferences?",
    )
    print(f"\n💬 [User CLI Input]:\n   \"{msg2.content}\"")
    time.sleep(0.5)
    reply2 = gateway.receive_message(msg2)
    print(f"\n🦞 [DevClaw Reply]:\n{reply2}")


def run_scenario_audit(gateway: DevClawGateway):
    print("\n" + "=" * 65)
    print("🛡️ SCENARIO 4: Local Audit Transparency")
    print("   OpenClaw logs every autonomous tool execution locally for user review.")
    print("=" * 65)

    logs = gateway.memory.get_recent_logs(limit=5)
    print(f"\n📋 Recent Local Action Audit Log ({len(logs)} actions logged):")
    for log in logs:
        print(f"  • [{log['timestamp']}] Channel: {log['channel'].upper()} | Skill: {log['action_name']} -> Status: {log['status']}")
        print(f"    Params: {log['parameters_json']}")
        print(f"    Summary: {log['result_summary'][:80]}...\n")


def run_all_scenarios():
    gateway = DevClawGateway()
    run_scenario_flight(gateway)
    run_scenario_inbox(gateway)
    run_scenario_memory(gateway)
    run_scenario_audit(gateway)
    print("\n" + "=" * 65)
    print("✨ All OpenClaw demonstration scenarios completed successfully!")
    print("=" * 65 + "\n")
