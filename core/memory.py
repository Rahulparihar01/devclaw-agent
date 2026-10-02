"""Local Persistent Memory Engine for DevClaw.

In OpenClaw, user data never leaves the local machine.
All facts, preferences, calendar entries, and action logs are stored in a local SQLite database.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class LocalMemory:
    """Manages local persistent storage using SQLite."""

    def __init__(self, db_path: str = "devclaw.db"):
        self.db_path = str(db_path)
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_db()
        self._seed_mock_data()

    def _get_connection(self) -> sqlite3.Connection:
        return self._conn

    def _init_db(self):
        """Creates the necessary tables if they do not exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 1. User preferences and facts
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    key TEXT NOT NULL UNIQUE,
                    value TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 2. Local Calendar events
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS calendar_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    location TEXT,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 3. Local Email Inbox (for mock demonstration)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS emails (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    body TEXT NOT NULL,
                    is_read INTEGER DEFAULT 0,
                    received_at TEXT NOT NULL
                )
            """)

            # 4. Action Audit Log (OpenClaw action transparency)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel TEXT NOT NULL,
                    action_name TEXT NOT NULL,
                    parameters_json TEXT NOT NULL,
                    result_summary TEXT NOT NULL,
                    status TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def _seed_mock_data(self):
        """Populates initial mock data so the demo works out-of-the-box."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Seed default preferences if empty
            cursor.execute("SELECT COUNT(*) FROM memories")
            if cursor.fetchone()[0] == 0:
                default_memories = [
                    ("preference", "seat_preference", "Window seat preferred"),
                    ("preference", "dietary_preference", "Vegetarian meal"),
                    ("contact", "manager_name", "Sarah Connor (Director of Eng)"),
                    ("travel", "frequent_flyer_number", "UA-88291047"),
                ]
                cursor.executemany(
                    "INSERT INTO memories (category, key, value) VALUES (?, ?, ?)",
                    default_memories,
                )

            # Seed demo emails if empty
            cursor.execute("SELECT COUNT(*) FROM emails")
            if cursor.fetchone()[0] == 0:
                demo_emails = [
                    (
                        "reservations@united.com",
                        "Flight Confirmation - SFO to JFK (Flight UA 442)",
                        "Hi Vinayak,\nYour flight UA 442 departs tomorrow from SFO Terminal 3 at 08:30 AM.\nConfirmation Code: CLAW77.\nOnline check-in is now open.",
                        0,
                        "2026-10-02 09:15:00",
                    ),
                    (
                        "alex@company.com",
                        "Project DevClaw Architecture Review",
                        "Hey, can we schedule a 30-minute sync this Friday at 3:00 PM to review the agent skills roadmap?",
                        0,
                        "2026-10-02 10:30:00",
                    ),
                    (
                        "newsletter@techbytes.io",
                        "Weekly Tech Roundup: Autonomous Personal Agents",
                        "Explore how local-first AI agents running on laptops are changing daily workflows...",
                        1,
                        "2026-10-01 14:00:00",
                    ),
                ]
                cursor.executemany(
                    "INSERT INTO emails (sender, subject, body, is_read, received_at) VALUES (?, ?, ?, ?, ?)",
                    demo_emails,
                )

            # Seed calendar events if empty
            cursor.execute("SELECT COUNT(*) FROM calendar_events")
            if cursor.fetchone()[0] == 0:
                demo_events = [
                    (
                        "Team Standup",
                        "2026-10-02 10:00:00",
                        "2026-10-02 10:30:00",
                        "Google Meet",
                        "Daily team sync",
                    )
                ]
                cursor.executemany(
                    "INSERT INTO calendar_events (title, start_time, end_time, location, description) VALUES (?, ?, ?, ?, ?)",
                    demo_events,
                )

            conn.commit()

    # --- Memory Operations ---

    def remember(self, category: str, key: str, value: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO memories (category, key, value, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET
                    value=excluded.value,
                    category=excluded.category,
                    updated_at=CURRENT_TIMESTAMP
            """,
                (category, key, value),
            )
            conn.commit()
            return True

    def recall(self, query: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if query:
                cursor.execute(
                    "SELECT category, key, value, updated_at FROM memories WHERE key LIKE ? OR value LIKE ? OR category LIKE ?",
                    (f"%{query}%", f"%{query}%", f"%{query}%"),
                )
            else:
                cursor.execute(
                    "SELECT category, key, value, updated_at FROM memories ORDER BY category, key"
                )
            return [dict(row) for row in cursor.fetchall()]

    # --- Email Operations ---

    def get_emails(self, unread_only: bool = False, query: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            sql = "SELECT id, sender, subject, body, is_read, received_at FROM emails WHERE 1=1"
            params = []
            if unread_only:
                sql += " AND is_read = 0"
            if query:
                sql += " AND (subject LIKE ? OR body LIKE ? OR sender LIKE ?)"
                params.extend([f"%{query}%", f"%{query}%", f"%{query}%"])
            sql += " ORDER BY received_at DESC"
            cursor.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]

    def mark_email_read(self, email_id: int):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE emails SET is_read = 1 WHERE id = ?", (email_id,))
            conn.commit()

    def send_email(self, to: str, subject: str, body: str) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO emails (sender, subject, body, is_read, received_at)
                VALUES ('me@user.local', ?, ?, 1, ?)
            """,
                (f"[Sent to {to}] {subject}", body, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            )
            conn.commit()
            return cursor.lastrowid

    # --- Calendar Operations ---

    def add_calendar_event(
        self, title: str, start_time: str, end_time: Optional[str] = None, location: str = "TBD", description: str = ""
    ) -> int:
        if not end_time:
            end_time = start_time
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM calendar_events WHERE title = ? AND start_time = ?", (title, start_time))
            existing = cursor.fetchone()
            if existing:
                return existing["id"]

            cursor.execute(
                """
                INSERT INTO calendar_events (title, start_time, end_time, location, description)
                VALUES (?, ?, ?, ?, ?)
            """,
                (title, start_time, end_time, location, description),
            )
            conn.commit()
            return cursor.lastrowid

    def list_calendar_events(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, title, start_time, end_time, location, description FROM calendar_events ORDER BY start_time ASC"
            )
            return [dict(row) for row in cursor.fetchall()]

    def reset_data(self):
        """Resets the SQLite database to clean initial seed data."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DROP TABLE IF EXISTS memories")
            cursor.execute("DROP TABLE IF EXISTS calendar_events")
            cursor.execute("DROP TABLE IF EXISTS emails")
            cursor.execute("DROP TABLE IF EXISTS audit_logs")
            conn.commit()
        self._init_db()
        self._seed_mock_data()

    # --- Audit Logging ---

    def log_action(
        self,
        channel: str,
        action_name: str,
        parameters: Dict[str, Any],
        result_summary: str,
        status: str = "SUCCESS",
    ):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO audit_logs (channel, action_name, parameters_json, result_summary, status)
                VALUES (?, ?, ?, ?, ?)
            """,
                (channel, action_name, json.dumps(parameters), result_summary, status),
            )
            conn.commit()

    def get_recent_logs(self, limit: int = 10) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, channel, action_name, parameters_json, result_summary, status, timestamp FROM audit_logs ORDER BY id DESC LIMIT ?",
                (limit,),
            )
            return [dict(row) for row in cursor.fetchall()]
