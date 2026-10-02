#!/usr/bin/env python3
"""Example script showing how Python code directly interacts with the real OpenClaw engine.

Demonstrates:
1. Connecting Python to the OpenClaw binary and Gateway.
2. Checking real OpenClaw engine version and system status.
3. Querying real OpenClaw AgentSkills (e.g. inbox-triage, weather, web_fetch).
4. Inspecting skill metadata from OpenClaw directly via Python.
"""

from openclaw_bridge import OpenClawBridge


def main():
    print("=" * 65)
    print("🦞 Using Real OpenClaw Engine directly from Python")
    print("=" * 65)

    claw = OpenClawBridge(profile="dev")

    # 1. Version Check
    print("\n1. 🔍 Querying Real OpenClaw Version:")
    version = claw.version()
    print(f"   Installed: {version}")

    # 2. System Status
    print("\n2. 📊 Fetching Real OpenClaw Gateway Status:")
    status = claw.status()
    # Print the first 12 lines of the real OpenClaw status table
    for line in status.strip().split("\n")[:15]:
        print(f"   {line}")

    # 3. Querying Real OpenClaw Skills
    print("\n3. 📦 Inspecting Real OpenClaw Skill: 'weather'")
    skill_info = claw.get_skill_info("weather")
    for line in skill_info.strip().split("\n")[:12]:
        print(f"   {line}")

    print("\n4. 📥 Inspecting Real OpenClaw Skill: 'taskflow-inbox-triage'")
    triage_info = claw.get_skill_info("taskflow-inbox-triage")
    for line in triage_info.strip().split("\n")[:12]:
        print(f"   {line}")

    print("\n" + "=" * 65)
    print("✅ Python successfully communicated with the real OpenClaw engine!")
    print("=" * 65)


if __name__ == "__main__":
    main()
