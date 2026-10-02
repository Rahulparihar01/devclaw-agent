"""Automated test suite verifying DevClaw core mechanics."""

import unittest
from core.agent import DevClawAgent
from core.gateway import DevClawGateway
from core.memory import LocalMemory
from core.models import ChannelMessage
from skills.registry import registry


class TestDevClaw(unittest.TestCase):

    def setUp(self):
        # Use in-memory SQLite or temporary db for isolated testing
        self.memory = LocalMemory(db_path=":memory:")
        self.gateway = DevClawGateway(memory=self.memory)

    def test_skills_registered(self):
        skills = registry.list_skills()
        skill_names = [s.name for s in skills]
        self.assertIn("search_emails", skill_names)
        self.assertIn("check_in_flight", skill_names)
        self.assertIn("add_calendar_event", skill_names)
        self.assertIn("remember_fact", skill_names)

    def test_local_memory_crud(self):
        self.memory.remember("preference", "coffee", "Oat milk latte")
        recalled = self.memory.recall(query="coffee")
        self.assertEqual(len(recalled), 1)
        self.assertEqual(recalled[0]["value"], "Oat milk latte")

    def test_flight_multi_step_flow(self):
        msg = ChannelMessage(
            channel="whatsapp",
            sender_id="+123456789",
            content="Find my flight in emails and check me in.",
        )
        reply = self.gateway.receive_message(msg)
        self.assertIn("Check-in: ✅ Completed", reply)
        self.assertIn("UA 442", reply)

        # Verify calendar event was created
        events = self.memory.list_calendar_events()
        flight_event = next((e for e in events if "UA 442" in e["title"]), None)
        self.assertIsNotNone(flight_event)

        # Verify audit logs
        logs = self.memory.get_recent_logs()
        action_names = [l["action_name"] for l in logs]
        self.assertIn("check_in_flight", action_names)

    def test_inbox_triage(self):
        msg = ChannelMessage(
            channel="whatsapp",
            sender_id="+123456789",
            content="which email important check and assist",
        )
        reply = self.gateway.receive_message(msg)
        self.assertIn("Inbox Triage Analysis", reply)
        self.assertIn("High Priority", reply)

    def test_read_first_mail(self):
        msg = ChannelMessage(
            channel="whatsapp",
            sender_id="+123456789",
            content="read first mail",
        )
        reply = self.gateway.receive_message(msg)
        self.assertIn("Email Content", reply)
        self.assertIn("Marked as Read", reply)

    def test_today_schedule_lists_events(self):
        msg = ChannelMessage(
            channel="whatsapp",
            sender_id="+123456789",
            content="give me today schedule",
        )
        reply = self.gateway.receive_message(msg)
        self.assertIn("event(s) scheduled", reply)
        self.assertIn("Team Standup", reply)

    def test_other_flight_details(self):
        msg = ChannelMessage(
            channel="whatsapp",
            sender_id="+123456789",
            content="other flight details",
        )
        reply = self.gateway.receive_message(msg)
        self.assertIn("only 1 scheduled flight", reply)

    def test_open_all_emails(self):
        msg = ChannelMessage(
            channel="whatsapp",
            sender_id="+123456789",
            content="need to open all the email",
        )
        reply = self.gateway.receive_message(msg)
        self.assertIn("Opened all", reply)
        self.assertIn("alex@company.com", reply)
        self.assertIn("reservations@united.com", reply)

    def test_reset_data(self):
        self.memory.add_calendar_event("Extra Meeting", "2026-10-04 10:00:00")
        self.assertEqual(len(self.memory.list_calendar_events()), 2)
        self.memory.reset_data()
        self.assertEqual(len(self.memory.list_calendar_events()), 1)


if __name__ == "__main__":
    unittest.main()
